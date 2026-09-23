"""Compute the key numbers the paper and site cite, from data/summary.json -> paper/numbers_auto.json.
Printed as a readable digest so the narrative can be written against real values."""
import json, sys
import numpy as np

D = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "../data/summary.json", encoding="utf-8"))
EXPS = D["experiments"]; LAB = D["labels"]
ORDER = ["qwen3:0.6b", "qwen3:1.7b", "qwen3:4b", "qwen3:8b", "qwen3:14b", "llama3.1:8b", "mistral:7b", "gemma4:latest", "gemma3:12b", "phi4:14b"]
MODELS = [m for m in ORDER if m in D["models"]]
IDX = {(r["model"], r["exp"], r["surface"], r["mode"], r["persona"]): r for r in D["results"]}


def row(m, e, s="novel", mo="fast", p="none"): return IDX.get((m, e, s, mo, p))


def mabs(m, s="novel", mo="fast", p="none"):
    v = [row(m, e, s, mo, p) for e in EXPS]
    v = [abs(r["bq"]) for r in v if r and r["bq"] is not None]
    return float(np.mean(v)) if len(v) == len(EXPS) else None


K = {}
for s in ("novel", "classic"):
    for mo in ("fast", "deliberate"):
        vals = {m: mabs(m, s, mo) for m in MODELS}
        good = [v for v in vals.values() if v is not None]
        K[f"avg_{s}_{mo}"] = float(np.mean(good)) if good else None
        K[f"rank_{s}_{mo}"] = sorted([(v, m) for m, v in vals.items() if v is not None])
K["avg_novel_advisor"] = float(np.mean([v for v in (mabs(m, "novel", "fast", "advisor") for m in MODELS) if v is not None]))

# per-bias: how many models show a significant human-direction effect (novel, fast)
sig = {}
for e in EXPS:
    n_sig = n_rev = 0; bqs = []
    for m in MODELS:
        r = row(m, e)
        if not r or r["bias"] is None: continue
        bqs.append(r["bq"])
        lo, hi = r["ci_lo"], r["ci_hi"]
        base = 0.5 if e == "disposition" else 0.0   # disposition: "human-direction" = prefers selling the winner
        if lo is not None and lo > base: n_sig += 1
        if hi is not None and hi < base: n_rev += 1
    sig[e] = {"n_pos_sig": n_sig, "n_neg_sig": n_rev, "median_bq": float(np.median(bqs)) if bqs else None, "n": len(bqs)}
K["per_bias_novel_fast"] = sig
sig2 = {}
for e in EXPS:
    bq = [row(m, e, "classic")["bq"] for m in MODELS if row(m, e, "classic") and row(m, e, "classic")["bq"] is not None]
    sig2[e] = {"median_bq": float(np.median(bq)) if bq else None}
K["per_bias_classic_fast"] = sig2
K["tests"] = D.get("tests"); K["acq"] = D.get("acquiescence_x50"); K["position"] = D.get("position_bias_first_option")
K["lambda"] = {m: {s: (row(m, "loss_aversion", s) or {}).get("parts", {}).get("lambda") for s in ("classic", "novel", "friend")} for m in MODELS}
K["qwen_ladder"] = {m: {"fast": mabs(m), "deliberate": mabs(m, "novel", "deliberate")} for m in MODELS if m.startswith("qwen3")}
json.dump(K, open("../paper/numbers_auto.json", "w", encoding="utf-8"), indent=1, default=float)

print(f"trials {D['n_trials']}  errors {D['n_errors']}")
for k in ("avg_novel_fast", "avg_novel_deliberate", "avg_classic_fast", "avg_classic_deliberate", "avg_novel_advisor"):
    print(f"{k:26s} {K[k]:.3f}")
print("\nrank novel fast:", [(m, round(v, 2)) for v, m in K["rank_novel_fast"]])
print("rank novel delib:", [(m, round(v, 2)) for v, m in K["rank_novel_deliberate"]])
print("\nper bias (novel fast): n models sig human-direction / sig reverse / median BQ   | classic median BQ")
for e in EXPS:
    s, c = sig[e], sig2[e]
    print(f"  {e:18s} {s['n_pos_sig']:2d} / {s['n_neg_sig']:2d} / {s['median_bq']:.2f}   | {c['median_bq'] if c['median_bq'] is None else round(c['median_bq'], 2)}")
print("\ntests:", json.dumps(D.get("tests"), indent=0))
print("\nlambda:", json.dumps(K["lambda"]))
print("\nacq x50:", json.dumps(D.get("acquiescence_x50")))
print("\nposition first:", D.get("position_bias_first_option"))
print("\nqwen ladder:", json.dumps(K["qwen_ladder"]))
pe = D.get("per_exp_tests", {})
for name, d in pe.items():
    print(f"\n{name}:", {e: (None if v['mean_a'] is None else (round(v['mean_a'], 2), round(v['mean_b'], 2))) for e, v in d.items()})
