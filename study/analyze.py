"""Turn raw trials into bias metrics, bootstrap CIs, and a summary.json for the site/paper.

Bias metrics (each is 0 for a perfectly consistent / "rational" agent):
  framing          P(sure | gain frame) - P(sure | loss frame)
  loss_aversion    lambda = X*/100, X* = prize where the isotonic acceptance curve crosses 50%; bias = lambda - 1
  anchoring        anchoring index = (median est | high anchor - median est | low anchor) / (high - low)
  sunk_cost        P(invest | sunk) - P(invest | control)
  disposition      P(sell winner). The prompt says the account is taxable and prospects are equal, so selling
                   the loser (harvesting the tax loss) is the normative choice: a rational seller scores 0.
  mental_accounting P(buy | lost cash) - P(buy | lost ticket)
  certainty        P(safe | certain) - P(safe | scaled)     (common-ratio / Allais-type violation)

Bias quotient (BQ) = model bias / human bias for the same measure. 0 = no bias, 1 = as biased as people.
"""
import json, math, sys
from collections import defaultdict
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.stats import fisher_exact, wilcoxon, binomtest

RNG = np.random.default_rng(7)
B = 1000  # bootstrap resamples

# Human baselines (sources in research/human-baselines.md)
HUMAN = {
    "framing": {"value": 0.72 - 0.22, "detail": "72% sure (gain) vs 22% sure (loss); Tversky & Kahneman 1981, N=152/155"},
    "loss_aversion": {"value": 2.25 - 1, "lambda": 2.25, "detail": "lambda = 2.25; Tversky & Kahneman 1992"},
    "anchoring": {"value": 0.49, "detail": "mean anchoring index 0.49; Jacowitz & Kahneman 1995"},
    "sunk_cost": {"value": 0.85 - 0.17, "detail": "85% invest (sunk) vs 17% (control); Arkes & Blumer 1985, N=48/60"},
    "disposition": {"value": 0.148 / (0.148 + 0.098),
                    "detail": "about 60% sell the winner, implied by PGR 0.148 vs PLR 0.098 (Odean 1998)"},
    "mental_accounting": {"value": 0.88 - 0.46, "detail": "88% buy (lost cash) vs 46% (lost ticket); Tversky & Kahneman 1981, N=183/200"},
    "certainty": {"value": 0.80 - 0.35, "detail": "80% sure $3000 vs 35% choose 25%-$3000 in scaled version; Kahneman & Tversky 1979, N=95"},
}
EXPS = list(HUMAN)
LABELS = {
    "framing": "Framing effect", "loss_aversion": "Loss aversion", "anchoring": "Anchoring",
    "sunk_cost": "Sunk-cost fallacy", "disposition": "Disposition effect",
    "mental_accounting": "Mental accounting", "certainty": "Certainty effect",
}


def load(path):
    recs = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            try:
                r = json.loads(line)
            except Exception:
                continue
            if "error" in r and r["id"] in recs:
                continue
            recs[r["id"]] = r
    df = pd.DataFrame(recs.values())
    return df


# ---------------------------------------------------------------- per-measure estimators
def p(sub, key, val):
    s = sub[sub.answer.notna()]
    return (s[key] == val).mean() if len(s) else np.nan


def diff_of_props(a, b):
    """a, b: boolean arrays. returns point, (lo, hi), Fisher exact two-sided p"""
    a, b = np.asarray(a, float), np.asarray(b, float)
    if len(a) == 0 or len(b) == 0:
        return np.nan, (np.nan, np.nan)
    pt = a.mean() - b.mean()
    bs = RNG.choice(a, (B, len(a))).mean(1) - RNG.choice(b, (B, len(b))).mean(1)
    diff_of_props.last_p = fisher_exact([[a.sum(), len(a) - a.sum()], [b.sum(), len(b) - b.sum()]])[1]
    return pt, tuple(np.percentile(bs, [2.5, 97.5]))


def fit_lambda(x, y):
    """Nonparametric loss-aversion coefficient.

    Acceptance rates per prize X are made monotone in X (isotonic regression, weighted by trial counts);
    X* is where that curve crosses 50%, interpolated on a log scale, and lambda = X*/100.
    Censored at the tested range: accepting even the $50 prize gives lambda = 0.5 (a lower bound),
    rejecting even the $600 prize gives lambda = 6 (an upper bound). Defined for every model, unlike a
    logistic fit, which has no threshold when acceptance does not rise with the prize.
    """
    from scipy.optimize import isotonic_regression
    x = np.asarray(x, float); y = np.asarray(y, float)
    levels = np.unique(x)
    rates = np.array([y[x == v].mean() for v in levels]); counts = np.array([(x == v).sum() for v in levels])
    iso = isotonic_regression(rates, weights=counts, increasing=True).x
    if iso[0] >= 0.5:
        return float(levels[0] / 100)
    if iso[-1] < 0.5:
        return float(levels[-1] / 100)
    i = int(np.argmax(iso >= 0.5))
    lo, hi = iso[i - 1], iso[i]
    t = (0.5 - lo) / (hi - lo) if hi > lo else 0.0
    xstar = math.exp(math.log(levels[i - 1]) + t * (math.log(levels[i]) - math.log(levels[i - 1])))
    return float(xstar / 100)


def measure(sub, exp):
    """sub: trials for one model × surface × mode × persona and experiment. Returns dict."""
    if exp == "framing":
        a = sub[sub.cond == "gain"].dropna(subset=["answer"]).answer.eq("sure")
        b = sub[sub.cond == "loss"].dropna(subset=["answer"]).answer.eq("sure")
        pt, ci = diff_of_props(a, b)
        return {"bias": pt, "ci": ci, "parts": {"sure_gain": a.mean(), "sure_loss": b.mean(), "p": diff_of_props.last_p}, "n": len(a) + len(b)}
    if exp == "sunk_cost":
        a = sub[sub.cond == "sunk"].dropna(subset=["answer"]).answer.eq("invest")
        b = sub[sub.cond == "control"].dropna(subset=["answer"]).answer.eq("invest")
        pt, ci = diff_of_props(a, b)
        return {"bias": pt, "ci": ci, "parts": {"invest_sunk": a.mean(), "invest_control": b.mean(), "p": diff_of_props.last_p}, "n": len(a) + len(b)}
    if exp == "mental_accounting":
        a = sub[sub.cond == "cash"].dropna(subset=["answer"]).answer.eq("buy")
        b = sub[sub.cond == "ticket"].dropna(subset=["answer"]).answer.eq("buy")
        pt, ci = diff_of_props(a, b)
        return {"bias": pt, "ci": ci, "parts": {"buy_cash": a.mean(), "buy_ticket": b.mean(), "p": diff_of_props.last_p}, "n": len(a) + len(b)}
    if exp == "certainty":
        a = sub[sub.cond == "certain"].dropna(subset=["answer"]).answer.eq("safe")
        b = sub[sub.cond == "scaled"].dropna(subset=["answer"]).answer.eq("safe")
        pt, ci = diff_of_props(a, b)
        return {"bias": pt, "ci": ci, "parts": {"safe_certain": a.mean(), "safe_scaled": b.mean(), "p": diff_of_props.last_p}, "n": len(a) + len(b)}
    if exp == "disposition":
        a = np.asarray(sub.dropna(subset=["answer"]).answer.eq("winner"), float)
        if len(a) == 0:
            return {"bias": np.nan, "ci": (np.nan, np.nan), "parts": {}, "n": 0}
        bs = RNG.choice(a, (B, len(a))).mean(1)
        return {"bias": a.mean(), "ci": tuple(np.percentile(bs, [2.5, 97.5])),
                "parts": {"sell_winner": a.mean(), "p": binomtest(int(a.sum()), len(a), 0.5).pvalue}, "n": len(a)}
    if exp == "loss_aversion":
        s = sub.dropna(subset=["answer"])
        x = s.x.astype(float).values
        y = s.answer.eq("accept").astype(float).values
        if len(x) == 0:
            return {"bias": np.nan, "ci": (np.nan, np.nan), "parts": {}, "n": 0}
        lam = fit_lambda(x, y)
        bs = []
        for _ in range(1000):
            idx = RNG.integers(0, len(x), len(x))
            bs.append(fit_lambda(x[idx], y[idx]))
        bs = np.array([v for v in bs if not np.isnan(v)])
        curve = s.assign(acc=y).groupby("x").acc.mean()
        return {"bias": lam - 1 if not np.isnan(lam) else np.nan,
                "ci": tuple(np.percentile(bs - 1, [2.5, 97.5])) if len(bs) else (np.nan, np.nan),
                "parts": {"lambda": lam, "accept_curve": {int(k): float(v) for k, v in curve.items()}}, "n": len(x)}
    if exp == "anchoring":
        s = sub.dropna(subset=["estimate"])
        s = s[pd.to_numeric(s.estimate, errors="coerce").notna()]
        est = {c: s[s.cond == c].estimate.astype(float).values for c in ("none", "low", "high")}
        anchors = {c: s[s.cond == c].anchor.dropna().astype(float).unique() for c in ("low", "high")}
        if len(est["low"]) == 0 or len(est["high"]) == 0:
            return {"bias": np.nan, "ci": (np.nan, np.nan), "parts": {}, "n": 0}
        span = anchors["high"][0] - anchors["low"][0]
        pt = (np.median(est["high"]) - np.median(est["low"])) / span
        bs = [(np.median(RNG.choice(est["high"], len(est["high"]))) - np.median(RNG.choice(est["low"], len(est["low"])))) / span
              for _ in range(B)]
        return {"bias": pt, "ci": tuple(np.percentile(bs, [2.5, 97.5])),
                "parts": {"median_none": float(np.median(est["none"])) if len(est["none"]) else None,
                          "median_low": float(np.median(est["low"])), "median_high": float(np.median(est["high"])),
                          "anchor_low": float(anchors["low"][0]), "anchor_high": float(anchors["high"][0])},
                "n": sum(len(v) for v in est.values())}
    raise ValueError(exp)


def clean(v):
    if isinstance(v, (np.floating, float)):
        return None if (v is None or np.isnan(v)) else round(float(v), 4)
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, dict):
        return {k: clean(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [clean(x) for x in v]
    return v


def analyze(df):
    rows = []
    for (model, surface, mode, persona), g in df.groupby(["model", "surface", "mode", "persona"]):
        for exp in EXPS:
            sub = g[g.exp == exp]
            if sub.empty:
                continue
            m = measure(sub, exp)
            h = HUMAN[exp]["value"]
            rows.append({"model": model, "surface": surface, "mode": mode, "persona": persona, "exp": exp,
                         "bias": m["bias"], "ci_lo": m["ci"][0], "ci_hi": m["ci"][1], "bq": m["bias"] / h if m["bias"] == m["bias"] else np.nan,
                         "n": m["n"], "parts": m["parts"]})
    return pd.DataFrame(rows)


def position_bias(df):
    c = df[df.position.notna()]
    return c.groupby("model").position.apply(lambda s: float((s == 0).mean())).to_dict()


def parse_rates(df):
    ok = df.apply(lambda r: "error" not in r or pd.isna(r.get("error")), axis=1)
    return df.assign(ok=ok).groupby("model").ok.mean().to_dict()


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "../data/trials.jsonl"
    out = sys.argv[2] if len(sys.argv) > 2 else "../data/summary.json"
    df = load(path)
    # exploratory "friend" wording of the loss-aversion bet (kept out of trials.jsonl so the neutral v2 wording
    # could be regenerated under the same trial ids); analysed as its own surface
    import os
    fpath = os.path.join(os.path.dirname(path), "friend_variant.jsonl")
    if os.path.exists(fpath):
        df = pd.concat([df, load(fpath)], ignore_index=True)
    if "error" not in df.columns:
        df["error"] = np.nan
    good = df[df.error.isna()]
    res = analyze(good)
    pd.set_option("display.width", 200)
    main = res[(res.surface == "novel") & (res["mode"] == "fast") & (res.persona == "none")]
    print(main.pivot(index="model", columns="exp", values="bq").round(2))
    # acquiescence: share accepting the negative-expected-value bet (win $50 vs lose $100), novel wording
    acq = {}
    la = good[(good.exp == "loss_aversion") & (good.x == 50) & (good.persona == "none")]
    for (m, mode, surf), g in la.groupby(["model", "mode", "surface"]):
        acq.setdefault(m, {})[f"{surf}_{mode}"] = float(g.answer.eq("accept").mean())

    def mean_abs(model, surface, mode, persona):
        sub = res[(res.model == model) & (res.surface == surface) & (res["mode"] == mode) & (res.persona == persona)]
        v = sub.bq.dropna().abs()
        return float(v.mean()) if len(v) == len(EXPS) else np.nan
    tests = {}
    models = sorted(good.model.unique())
    for name, a, b in [("textbook_vs_novel", ("classic", "fast", "none"), ("novel", "fast", "none")),
                       ("fast_vs_deliberate", ("novel", "fast", "none"), ("novel", "deliberate", "none")),
                       ("none_vs_advisor", ("novel", "fast", "none"), ("novel", "fast", "advisor")),
                       ("textbook_vs_novel_deliberate", ("classic", "deliberate", "none"), ("novel", "deliberate", "none"))]:
        pa = np.array([mean_abs(m, *a) for m in models]); pb = np.array([mean_abs(m, *b) for m in models])
        ok = ~(np.isnan(pa) | np.isnan(pb))
        if ok.sum() >= 5:
            w = wilcoxon(pa[ok], pb[ok])
            tests[name] = {"n_models": int(ok.sum()), "mean_a": float(pa[ok].mean()), "mean_b": float(pb[ok].mean()),
                           "n_increase": int((pb[ok] > pa[ok]).sum()), "wilcoxon_p": float(w.pvalue)}
    # the same comparisons experiment by experiment (signed bias quotients, paired over models)
    per_exp = {}
    for name, a, b in [("fast_vs_deliberate", ("classic", "fast", "none"), ("classic", "deliberate", "none")),
                       ("fast_vs_deliberate_novel", ("novel", "fast", "none"), ("novel", "deliberate", "none")),
                       ("textbook_vs_novel", ("classic", "fast", "none"), ("novel", "fast", "none"))]:
        for e in EXPS:
            def g(model, sp):
                sub = res[(res.model == model) & (res.exp == e) & (res.surface == sp[0]) & (res["mode"] == sp[1]) & (res.persona == sp[2])]
                return float(sub.bq.iloc[0]) if len(sub) and pd.notna(sub.bq.iloc[0]) else np.nan
            va = np.array([g(m, a) for m in models]); vb = np.array([g(m, b) for m in models])
            ok = ~(np.isnan(va) | np.isnan(vb))
            per_exp.setdefault(name, {})[e] = {"mean_a": float(np.nanmean(va[ok])) if ok.any() else None,
                                               "mean_b": float(np.nanmean(vb[ok])) if ok.any() else None, "n": int(ok.sum())}
    summary = {
        "human": HUMAN, "labels": LABELS, "experiments": EXPS,
        "n_trials": int(len(good)), "n_errors": int(df.error.notna().sum()),
        "models": sorted(good.model.unique().tolist()),
        "position_bias_first_option": clean(position_bias(good)),
        "results": [clean(r) for r in res.to_dict("records")],
        "acquiescence_x50": clean(acq), "tests": clean(tests), "per_exp_tests": clean(per_exp),
    }
    with open(out, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1)
    print(f"wrote {out}: {len(res)} rows, {len(good)} trials, {summary['n_errors']} errors")
