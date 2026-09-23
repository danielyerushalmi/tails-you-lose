"""Generate trials and run them against local Ollama models.

Usage:
  python run.py --models qwen3:8b llama3.1:8b --n 30 --out ../data/trials.jsonl
  python run.py --pilot            # tiny sanity run, prints a few raw responses

Resumable: each trial has a deterministic id; ids already present in the output
file are skipped, so the script can be killed and restarted at any time.
"""
import argparse, asyncio, json, os, random, sys, time
import httpx
import experiments as E

OLLAMA = "http://127.0.0.1:11434/api/chat"
TEMPERATURE = 0.8

SYSTEM = {
    "none": (
        "You are taking part in a decision-making study. Read the scenario and answer with the choice you "
        "yourself would make. There are no right or wrong answers. Respond only in the requested JSON format."
    ),
    "advisor": (
        "You are an experienced, CFA-certified financial advisor known for disciplined, rational decisions. You are "
        "taking part in a decision-making study. Read the scenario and answer with the choice you yourself would make. "
        "Respond only in the requested JSON format."
    ),
}
MODE_INSTR = {
    "fast": "Answer immediately.",
    "deliberate": "First think the decision through briefly in the \"reasoning\" field (2-4 sentences), then give your final answer.",
}


# ------------------------------------------------------------------ trial generation
def _choice_trial(exp, cond, surface, text, options, question=None):
    """options: dict semantic_key -> display text (order randomised later)."""
    return {"exp": exp, "cond": cond, "surface": surface, "kind": "choice",
            "text": text, "options": options, "question": question}


def base_trials():
    T = []
    # E1 framing
    for s, d in E.FRAMING.items():
        for frame in ("gain", "loss"):
            T.append(_choice_trial("framing", frame, s, d["stem"], d[frame], d["question"]))
    # E2 loss aversion
    for s in ("classic", "novel"):
        for x in E.LOSS_X:
            t = _choice_trial("loss_aversion", f"x{x}", s, E.LOSS_AVERSION[s].format(x=x), E.LOSS_AVERSION["options"])
            t["x"] = x
            T.append(t)
    # E3 anchoring
    for s, d in E.ANCHORING.items():
        for cond, a in E.ANCHORS.items():
            if s == "classic" and a == 150:
                a = 65  # wheel of fortune only runs 0-100; classic T&K anchors were 10 and 65
            parts = [d.get("context", "")]
            if a is not None:
                parts += [d["anchor_line"].format(a=a), d["compare"].format(a=a)]
            parts.append(d["estimate"])
            T.append({"exp": "anchoring", "cond": cond, "surface": s, "kind": "anchor",
                      "anchor": a, "text": " ".join(p for p in parts if p)})
    # E4 sunk cost
    for s in ("classic", "novel"):
        for cond in ("sunk", "control"):
            T.append(_choice_trial("sunk_cost", cond, s, E.SUNK_COST[s][cond], E.SUNK_COST["options"]))
    # E5 disposition (single condition; which name/position is the winner is randomised per trial)
    for s in ("classic", "novel"):
        T.append({"exp": "disposition", "cond": "main", "surface": s, "kind": "disposition"})
    # E6 mental accounting
    for s in ("classic", "novel"):
        for cond in ("cash", "ticket"):
            T.append(_choice_trial("mental_accounting", cond, s, E.MENTAL_ACCOUNTING[s][cond], E.MENTAL_ACCOUNTING["options"]))
    # E7 certainty / common ratio
    for s, d in E.CERTAINTY.items():
        for cond in ("certain", "scaled"):
            T.append(_choice_trial("certainty", cond, s, d["stem"], d[cond], d["question"]))
    return T


def expand(models, n, modes=("fast", "deliberate"), persona_extra=True):
    """Full design. Advisor persona only on (novel, fast) to keep the run tractable."""
    out = []
    for m in models:
        for bt in base_trials():
            cells = [(mode, "none") for mode in modes]
            if persona_extra and bt["surface"] == "novel":
                cells.append(("fast", "advisor"))
            for mode, persona in cells:
                for i in range(n):
                    tid = f"{m}|{bt['exp']}|{bt['cond']}|{bt['surface']}|{mode}|{persona}|{i}"
                    out.append({**bt, "model": m, "mode": mode, "persona": persona, "rep": i, "id": tid})
    return out


# ------------------------------------------------------------------ prompt building
def build(trial):
    """Returns (user_prompt, json_schema, label_map) with randomised option order."""
    rng = random.Random(trial["id"])  # deterministic per trial
    mode = trial["mode"]
    reasoning = {"reasoning": {"type": "string"}} if mode == "deliberate" else {}

    if trial["kind"] == "anchor":
        a = trial["anchor"]
        props = dict(reasoning)
        if a is not None:
            props["higher_or_lower"] = {"type": "string", "enum": ["higher", "lower"]}
        props["estimate"] = {"type": "number"}
        schema = {"type": "object", "properties": props, "required": list(props)}
        fields = ", ".join(f'"{k}"' for k in props)
        prompt = f"{trial['text']}\n\n{MODE_INSTR[mode]} Reply as JSON with fields {fields}."
        return prompt, schema, None

    if trial["kind"] == "disposition":
        d = E.DISPOSITION
        n1, n2 = d["names"][trial["surface"]]
        winner_first = rng.random() < 0.5
        w, l = (n1, n2) if winner_first else (n2, n1)
        if trial["surface"] == "classic":
            text = d["classic"].format(n1=n1, n2=n2, d1="up 30%" if winner_first else "down 30%",
                                        d2="down 30%" if winner_first else "up 30%")
        else:
            text = d["novel"].format(n1=n1, n2=n2, v1="gained" if winner_first else "lost",
                                      v2="lost" if winner_first else "gained")
        options = {"winner": f"Sell {w}", "loser": f"Sell {l}"}
        trial = {**trial, "text": text, "options": options, "question": None, "winner_first": winner_first}
    else:
        options = trial["options"]

    keys = list(options)
    rng.shuffle(keys)
    labels = ["A", "B", "C", "D"][: len(keys)]
    label_map = dict(zip(labels, keys))
    lines = [trial["text"], ""]
    for lab, k in label_map.items():
        lines.append(f"Option {lab}: {options[k]}")
    if trial.get("question"):
        lines += ["", trial["question"]]
    lines += ["", f"{MODE_INSTR[mode]} Reply as JSON with " + ('fields "reasoning", "choice"' if reasoning else 'field "choice"')
              + f" where choice is one of {', '.join(labels)}."]
    props = dict(reasoning)
    props["choice"] = {"type": "string", "enum": labels}
    schema = {"type": "object", "properties": props, "required": list(props)}
    extra = {"winner_first": trial.get("winner_first")} if trial["kind"] == "disposition" else {}
    return "\n".join(lines), schema, {"labels": label_map, **extra}


# ------------------------------------------------------------------ running
async def run_one(client, trial, sem):
    prompt, schema, meta = build(trial)
    seed = random.Random(trial["id"] + "seed").randrange(2**31)
    body = {
        "model": trial["model"],
        "messages": [{"role": "system", "content": SYSTEM[trial["persona"]]},
                     {"role": "user", "content": prompt}],
        "format": schema,
        "stream": False,
        "options": {"temperature": TEMPERATURE, "seed": seed,
                    "num_predict": 1200 if trial["mode"] == "deliberate" else 80},
        "keep_alive": "30m",
    }
    if trial["model"].startswith(("qwen3", "gemma4")):
        # these models think by default: keep hidden chain-of-thought off so every model faces the same
        # format (gemma4 otherwise spends the whole fast-mode token budget thinking and returns nothing)
        body["think"] = False
    async with sem:
        t0 = time.time()
        for attempt in range(3):
            try:
                r = await client.post(OLLAMA, json=body, timeout=300)
                r.raise_for_status()
                raw = r.json()["message"]["content"]
                break
            except Exception as e:  # transient server errors: retry, then record failure
                raw, err = None, repr(e)
                await asyncio.sleep(2 * (attempt + 1))
        dt = time.time() - t0
    rec = {k: trial[k] for k in ("id", "model", "exp", "cond", "surface", "mode", "persona", "rep")}
    rec.update({"x": trial.get("x"), "anchor": trial.get("anchor"), "raw": raw, "latency": round(dt, 2)})
    if raw is None:
        rec["error"] = err
        return rec
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError:
        rec["error"] = "parse"
        return rec
    rec["reasoning"] = obj.get("reasoning")
    if trial["kind"] == "anchor":
        rec["estimate"] = obj.get("estimate")
        rec["higher_or_lower"] = obj.get("higher_or_lower")
    else:
        lab = obj.get("choice")
        rec["label"] = lab
        rec["position"] = list(meta["labels"]).index(lab) if lab in meta["labels"] else None
        rec["answer"] = meta["labels"].get(lab)
        if "winner_first" in meta:
            rec["winner_first"] = meta["winner_first"]
    return rec


async def run(trials, out_path, concurrency):
    done = set()
    if os.path.exists(out_path):
        with open(out_path, encoding="utf-8") as f:
            for line in f:
                try:
                    r = json.loads(line)
                    if "error" not in r:  # failed trials are retried; analysis keeps the last good record per id
                        done.add(r["id"])
                except Exception:
                    pass
    todo = [t for t in trials if t["id"] not in done]
    print(f"{len(trials)} trials, {len(done)} already done, {len(todo)} to run", flush=True)
    sem = asyncio.Semaphore(concurrency)
    async with httpx.AsyncClient() as client:
        # one model at a time so Ollama isn't thrashing weights in and out of VRAM
        by_model = {}
        for t in todo:
            by_model.setdefault(t["model"], []).append(t)
        for m, ts in by_model.items():
            t0 = time.time()
            n_ok = 0
            with open(out_path, "a", encoding="utf-8") as f:
                for i in range(0, len(ts), 200):
                    chunk = ts[i:i + 200]
                    recs = await asyncio.gather(*(run_one(client, t, sem) for t in chunk))
                    for r in recs:
                        f.write(json.dumps(r, ensure_ascii=False) + "\n")
                        n_ok += "error" not in r
                    f.flush()
                    el = time.time() - t0
                    print(f"[{m}] {i + len(chunk)}/{len(ts)} ok={n_ok} {el:.0f}s", flush=True)
            print(f"MODEL_DONE {m} {time.time() - t0:.0f}s", flush=True)
    print("RUN_DONE", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="+", default=["qwen3:8b"])
    ap.add_argument("--n", type=int, default=30)
    ap.add_argument("--out", default="../data/trials.jsonl")
    ap.add_argument("--concurrency", type=int, default=4)
    ap.add_argument("--pilot", action="store_true")
    a = ap.parse_args()
    if a.pilot:
        trials = expand(a.models, 1)
        rng = random.Random(0)
        sample = rng.sample(trials, min(12, len(trials)))
        async def pilot():
            sem = asyncio.Semaphore(a.concurrency)
            async with httpx.AsyncClient() as c:
                recs = await asyncio.gather(*(run_one(c, t, sem) for t in sample))
            for t, r in zip(sample, recs):
                print("-" * 80)
                print(build(t)[0])
                print(">>>", json.dumps({k: r.get(k) for k in ("model", "exp", "cond", "mode", "persona", "answer", "estimate", "higher_or_lower", "error", "latency")}))
                print("RAW:", (r.get("raw") or "")[:300])
        asyncio.run(pilot())
        sys.exit()
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    asyncio.run(run(expand(a.models, a.n), a.out, a.concurrency))
