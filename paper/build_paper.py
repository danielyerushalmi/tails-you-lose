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
    "qwen3:0.6b": ("Qwen3 0.6B", "Alibaba", "0.6B", "qwen3:0.6b"), "qwen3:1.7b": ("Qwen3 1.7B", "Alibaba", "1.7B", "qwen3:1.7b"),
    "qwen3:4b": ("Qwen3 4B", "Alibaba", "4B", "qwen3:4b"), "qwen3:8b": ("Qwen3 8B", "Alibaba", "8B", "qwen3:8b"),
    "qwen3:14b": ("Qwen3 14B", "Alibaba", "14B", "qwen3:14b"), "llama3.1:8b": ("Llama 3.1 8B", "Meta", "8B", "llama3.1:8b"),
    "mistral:7b": ("Mistral 7B", "Mistral AI", "7B", "mistral:7b"), "gemma4:latest": ("Gemma 4", "Google", "8B", "gemma4:latest"),
    "gemma3:12b": ("Gemma 3 12B", "Google", "12B", "gemma3:12b"), "phi4:14b": ("Phi-4 14B", "Microsoft", "14B", "phi4:14b"),
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
    return f"<table><thead><tr><th>Model</th><th>Developer</th><th>Parameters</th><th>Ollama tag</th></tr></thead><tbody>{rows}</tbody></table><p class='small'>Table 1. The ten models. Qwen3 0.6B to 14B form the within-family size ladder.</p>"


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
        out.append(f"<p class='small'><b>{LAB.get(p['exp'], p['exp'])}</b> · condition <span class='mono'>{p['cond']}</span> · {'textbook' if p['surface'] == 'classic' else 'new financial'} wording</p><div class='prompt'>{html.escape(p['prompt'])}</div>")
    return "\n".join(out)


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
