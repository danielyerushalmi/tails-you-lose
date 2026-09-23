"""Assemble paper.html from template.html + results.html + summary.json, then render paper.pdf.

Every number in the paper comes from summary.json via the K dict below; prose that cites
numbers uses {{KEY}} tokens so a re-run of the analysis updates the paper automatically.
"""
import html, json, re, subprocess, sys, os
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(HERE, "..", "data", "summary.json"), encoding="utf-8"))
P = json.load(open(os.path.join(HERE, "prompts.json"), encoding="utf-8"))

ORDER = ["qwen3:0.6b", "qwen3:1.7b", "qwen3:4b", "qwen3:8b", "qwen3:14b", "llama3.1:8b", "mistral:7b", "gemma4:latest", "gemma3:12b", "phi4:14b"]
META = {
    "qwen3:0.6b": ("Qwen3 0.6B", "Alibaba", "0.75B", "qwen3:0.6b"), "qwen3:1.7b": ("Qwen3 1.7B", "Alibaba", "2.0B", "qwen3:1.7b"),
    "qwen3:4b": ("Qwen3 4B", "Alibaba", "4.0B", "qwen3:4b"), "qwen3:8b": ("Qwen3 8B", "Alibaba", "8.2B", "qwen3:8b"),
    "qwen3:14b": ("Qwen3 14B", "Alibaba", "14.8B", "qwen3:14b"), "llama3.1:8b": ("Llama 3.1 8B", "Meta", "8.0B", "llama3.1:8b"),
    "mistral:7b": ("Mistral 7B", "Mistral AI", "7.2B", "mistral:7b"), "gemma4:latest": ("Gemma 4", "Google", "8.0B", "gemma4:latest"),
    "gemma3:12b": ("Gemma 3 12B", "Google", "12.2B", "gemma3:12b"), "phi4:14b": ("Phi-4 14B", "Microsoft", "14.7B", "phi4:14b"),
}
MODELS = [m for m in ORDER if m in D["models"]]
EXPS = D["experiments"]; LAB = D["labels"]


def row(m, e, surface="novel", mode="fast", persona="none"):
    for r in D["results"]:
        if (r["model"], r["exp"], r["surface"], r["mode"], r["persona"]) == (m, e, surface, mode, persona):
            return r


def mabs(m, surface="novel", mode="fast", persona="none"):
    v = [row(m, e, surface, mode, persona) for e in EXPS]
    v = [abs(r["bq"]) for r in v if r and r["bq"] is not None]
    return sum(v) / len(v) if len(v) == len(EXPS) else None


def f2(v): return "n/a" if v is None else f"{v:.2f}"
def pct(v): return "n/a" if v is None else f"{round(v * 100)}%"


def table_models():
    rows = "".join(f"<tr><td>{META[m][0]}</td><td>{META[m][1]}</td><td class='n'>{META[m][2]}</td><td class='mono'>{META[m][3]}</td></tr>" for m in MODELS)
    return f"<table><thead><tr><th>Model</th><th>Developer</th><th>Parameters</th><th>Ollama tag</th></tr></thead><tbody>{rows}</tbody></table><p class='small'>Table 1. The ten models, with parameter counts as reported by Ollama (model names use the developers' nominal sizes). Qwen3 0.6B to 14B form the within-family size ladder. All are 4-bit Q4_K_M quantizations.</p>"


def table_experiments():
    E = [
        ("Framing", "Sure vs. risky plan; outcomes described as gains or as losses", "P(sure | gain) − P(sure | loss)", "72% − 22% = 0.50"),
        ("Loss aversion", "50/50 bet: lose $100 or win $X, X from $50 to $600", "λ − 1, λ = X*/$100", "λ = 2.25"),
        ("Anchoring", "Estimate after a random anchor (low or high)", "anchoring index", "0.49"),
        ("Sunk cost", "Spend the last budget on a doomed project, with or without prior spending", "P(invest | sunk) − P(invest | none)", "85% − 17% = 0.68"),
        ("Disposition", "Must sell one of two equally promising stocks, one up 30%, one down 30%", "P(sell winner); normative = 0", "≈ 0.60 (Odean 1998)"),
        ("Mental accounting", "Rebuy after losing the ticket vs. losing the same amount of cash", "P(buy | cash) − P(buy | ticket)", "88% − 46% = 0.42"),
        ("Certainty", "$3,000 sure vs. 80% × $4,000, and both chances divided by 4", "P(safe | certain) − P(safe | scaled)", "80% − 35% = 0.45"),
    ]
    rows = "".join(f"<tr><td>{a}</td><td>{b}</td><td>{c}</td><td class='n'>{d}</td></tr>" for a, b, c, d in E)
    return f"<table><thead><tr><th>Bias</th><th>Task</th><th>Bias measure (0 = consistent)</th><th>Human</th></tr></thead><tbody>{rows}</tbody></table><p class='small'>Table 2. Experiments, measures and human reference values.</p>"


def table_results(surface="novel", mode="fast", persona="none", caption=""):
    head = "".join(f"<th>{LAB[e].replace(' effect', '').replace('-cost fallacy', ' cost')}</th>" for e in EXPS)
    body = ""
    ms = sorted(MODELS, key=lambda m: 9 if mabs(m, surface, mode, persona) is None else mabs(m, surface, mode, persona))
    for m in ms:
        cells = ""
        for e in EXPS:
            r = row(m, e, surface, mode, persona)
            cells += f"<td class='n'>{f2(r['bq']) if r else 'n/a'}</td>"
        body += f"<tr><td>{META[m][0]}</td>{cells}<td class='n'><b>{f2(mabs(m, surface, mode, persona))}</b></td></tr>"
    return f"<table><thead><tr><th>Model</th>{head}<th>Mean |BQ|</th></tr></thead><tbody>{body}</tbody></table><p class='small'>{caption}</p>"


def appendix():
    out = [f"<p class='small'>System prompt (no persona):</p><div class='prompt'>{html.escape(P['system']['none'])}</div>",
           f"<p class='small'>System prompt (advisor persona):</p><div class='prompt'>{html.escape(P['system']['advisor'])}</div>",
           "<p class='small'>User prompts below are shown in fast mode, with one example option order. In thinks-first mode, the last line instead asks the model to reason briefly in a \"reasoning\" field before answering. The loss-aversion prompts are shown for X = $150; X ran over $50, 100, 125, 150, 200, 250, 300, 400 and 600.</p>"]
    for p in P["prompts"]:
        out.append(f"<p class='small'><b>{LAB.get(p['exp'], p['exp'])}</b> · condition <span class='mono'>{p['cond']}</span> · { {'classic': 'textbook', 'novel': 'new financial', 'friend': 'exploratory friend'}[p['surface']] } wording</p><div class='prompt'>{html.escape(p['prompt'])}</div>")
    return "\n".join(out)



def tokens():
    """Every number the prose cites, computed from summary.json."""
    import statistics as st
    T = {}
    n = lambda v, d=2: "n/a" if v is None else f"{v:.{d}f}"
    avg = lambda xs: (sum(xs) / len(xs)) if xs else None
    def mean_over(s, mo, p="none"):
        v = [mabs(m, s, mo, p) for m in MODELS]; v = [x for x in v if x is not None]
        return avg(v), len(v)
    for key, (s, mo, p) in {"NF": ("novel", "fast", "none"), "CF": ("classic", "fast", "none"), "ND": ("novel", "deliberate", "none"),
                            "CD": ("classic", "deliberate", "none"), "ADV": ("novel", "fast", "advisor")}.items():
        a, k = mean_over(s, mo, p); T[f"AVG_{key}"] = n(a); T[f"AVG_{key}_RAW"] = a
    ranked = sorted([(mabs(m), m) for m in MODELS if mabs(m) is not None])
    T["BEST_NF"], T["BEST_NF_V"] = META[ranked[0][1]][0], n(ranked[0][0])
    T["WORST_NF"], T["WORST_NF_V"] = META[ranked[-1][1]][0], n(ranked[-1][0])
    rd = sorted([(mabs(m, "novel", "deliberate"), m) for m in MODELS if mabs(m, "novel", "deliberate") is not None])
    T["BEST_ND"], T["BEST_ND_V"] = META[rd[0][1]][0], n(rd[0][0])
    tests = D.get("tests", {})
    for key, name in {"TVN": "textbook_vs_novel", "FVD": "fast_vs_deliberate", "ADVT": "none_vs_advisor"}.items():
        t = tests.get(name, {})
        T[f"N_{key}"] = t.get("n_models", "n/a"); T[f"N_{key}_INC"] = t.get("n_increase", "n/a")
        T[f"N_{key}_DEC"] = (t["n_models"] - t["n_increase"]) if t else "n/a"
        T[f"P_{key}"] = n(t.get("wilcoxon_p"), 3) if t else "n/a"
    pe = D.get("per_exp_tests", {})
    for e in EXPS:
        for key, name in {"FD": "fast_vs_deliberate_novel", "TN": "textbook_vs_novel", "AD": "none_vs_advisor"}.items():
            v = pe.get(name, {}).get(e, {})
            T[f"{key}_{e.upper()}_A"] = n(v.get("mean_a")); T[f"{key}_{e.upper()}_B"] = n(v.get("mean_b"))
    # anchoring
    anc = {m: row(m, "anchoring") for m in MODELS}
    T["N_ANCH_OVER_HUMAN"] = sum(1 for r in anc.values() if r and r["bq"] is not None and r["bq"] > 1)
    T["N_ANCH_IMMUNE"] = sum(1 for r in anc.values() if r and r["bq"] is not None and abs(r["bq"]) < 0.25)
    T["ANCH_IMMUNE_NAMES"] = ", ".join(META[m][0] for m, r in anc.items() if r and r["bq"] is not None and abs(r["bq"]) < 0.25)
    ancc = [row(m, "anchoring", "classic") for m in MODELS]
    T["N_ANCH_CLASSIC_LOW"] = sum(1 for r in ancc if r and r["bq"] is not None and abs(r["bq"]) < 0.25)
    # sunk cost: models that almost never invest in either version
    sc = [row(m, "sunk_cost") for m in MODELS]
    T["N_SUNK_NEVER"] = sum(1 for r in sc if r and r["parts"]["invest_sunk"] <= 0.05 and r["parts"]["invest_control"] <= 0.05)
    # disposition
    dw = [row(m, "disposition")["parts"]["sell_winner"] for m in MODELS if row(m, "disposition")]
    T["DISP_MEDIAN"] = f"{round(st.median(dw) * 100)}%"; T["N_DISP_LOSER"] = sum(1 for v in dw if v < 0.5)
    # loss aversion by wording
    for s, key in (("classic", "C"), ("novel", "N"), ("friend", "F")):
        lam = [row(m, "loss_aversion", s)["parts"]["lambda"] for m in MODELS if row(m, "loss_aversion", s) and row(m, "loss_aversion", s)["parts"].get("lambda") is not None]
        T[f"N_LAM_{key}"] = len(lam)
        T[f"N_LAM_BELOW_{key}"] = sum(1 for v in lam if v < 0.9)
        T[f"N_LAM_NEUTRAL_{key}"] = sum(1 for v in lam if 0.9 <= v < 1.5)
        T[f"N_LAM_AVERSE_{key}"] = sum(1 for v in lam if v >= 1.5)
    acq = D.get("acquiescence_x50", {})
    for key, col in {"ACQ_C": "classic_fast", "ACQ_N": "novel_fast", "ACQ_F": "friend_fast", "ACQ_CD": "classic_deliberate", "ACQ_ND": "novel_deliberate", "ACQ_FD": "friend_deliberate"}.items():
        v = [acq[m][col] for m in MODELS if m in acq and col in acq[m]]
        T[key] = f"{round(avg(v) * 100)}%" if v else "n/a"
        T[key + "_N100"] = sum(1 for x in v if x >= 0.9)
    pos = D.get("position_bias_first_option", {})
    T["POS_MIN"] = f"{round(min(pos.values()) * 100)}%"; T["POS_MAX"] = f"{round(max(pos.values()) * 100)}%"
    for m in [m for m in MODELS if m.startswith("qwen3")]:
        k = m.split(":")[1].replace(".", "").upper()
        T[f"Q{k}_F"] = n(mabs(m)); T[f"Q{k}_D"] = n(mabs(m, "novel", "deliberate"))
    T["N_FRIEND_TRIALS"] = f"{D.get('n_friend_trials', 0):,}"
    rc = D.get("reasoning_checks", {})
    T["DISP_N"], T["DISP_TAX"], T["DISP_TAX_LOSER"] = rc.get("disp_n"), rc.get("disp_tax"), rc.get("disp_tax_loser")
    T["DISP_TAX_PCT"] = f"{round(rc['disp_tax'] / rc['disp_n'] * 100)}%" if rc.get("disp_n") else "n/a"
    T["ANCH_N"], T["ANCH_CALC"] = rc.get("anch_n"), rc.get("anch_calc")
    T["ANCH_CALC_FAIR"] = f"{round(rc['anch_calc_fair'] * 100)}%" if rc.get("anch_calc_fair") is not None else "n/a"
    T["ANCH_NOCALC_FAIR"] = f"{round(rc['anch_nocalc_fair'] * 100)}%" if rc.get("anch_nocalc_fair") is not None else "n/a"
    return {k: v for k, v in T.items() if not k.endswith("_RAW")}

def main():
    K = json.load(open(os.path.join(HERE, "numbers.json"), encoding="utf-8")) if os.path.exists(os.path.join(HERE, "numbers.json")) else {}
    tpl = open(os.path.join(HERE, "template.html"), encoding="utf-8").read()
    results = open(os.path.join(HERE, "results.html"), encoding="utf-8").read() if os.path.exists(os.path.join(HERE, "results.html")) else "<h2>Results</h2><p>(pending)</p>"
    T = {
        "DATE": K.get("DATE", date.today().strftime("%B %Y")),
        "N_TRIALS": f"{D['n_trials']:,}", "N_ERRORS": f"{D['n_errors']:,}",
        "REPO_URL": K.get("REPO_URL", "github.com/danielyerushalmi/tails-you-lose"), "SITE_URL": K.get("SITE_URL", ""),
        "TABLE_MODELS": table_models(), "TABLE_EXPERIMENTS": table_experiments(),
        "TABLE_RESULTS_MAIN": table_results(caption="Table 3. Bias quotient by model and bias, new financial wording, fast answers. 1.00 = as biased as people; negative = biased in the opposite direction. Sorted by mean absolute BQ."),
        "TABLE_RESULTS_CLASSIC": table_results("classic", caption="Table 4. The same measures on the textbook wording (fast answers)."),
        "TABLE_RESULTS_DELIB": table_results("novel", "deliberate", caption="Table 5. New financial wording, thinks-first answers."),
        "APPENDIX_PROMPTS": appendix(),
        "SEC_LIM": K.get("SEC_LIM", "6"), "SEC_CONC": K.get("SEC_CONC", "7"), "SEC_FRIEND": K.get("SEC_FRIEND", "4.6"),
        "ABSTRACT": K.get("ABSTRACT", "(pending)"), "CONCLUSION": K.get("CONCLUSION", "<p>(pending)</p>"),
    }
    T.update(tokens())
    T.update({k: v for k, v in K.items() if k not in T})
    doc = tpl.replace("{{RESULTS}}", results)
    # two passes: tokens inside the results/abstract text get filled on the second pass
    for _ in range(2):
        doc = re.sub(r"\{\{([A-Z0-9_]+)\}\}", lambda mo: str(T.get(mo.group(1), mo.group(0))), doc)
    left = sorted(set(re.findall(r"\{\{([A-Z0-9_]+)\}\}", doc)))
    if left:
        print("UNFILLED TOKENS:", left)
    open(os.path.join(HERE, "paper.html"), "w", encoding="utf-8").write(doc)
    print("wrote paper.html")


if __name__ == "__main__":
    main()
