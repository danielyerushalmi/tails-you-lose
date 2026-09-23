"""Paper figures from data/summary.json (same palette as the site)."""
import json, math, os, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm

SUMMARY = sys.argv[1] if len(sys.argv) > 1 else "../data/summary.json"
OUT = sys.argv[2] if len(sys.argv) > 2 else "../paper/fig"
os.makedirs(OUT, exist_ok=True)
D = json.load(open(SUMMARY, encoding="utf-8"))

INK = "#16241e"; INK2 = "#4a5a53"; RULE = "#b9cfc6"; RED = "#c0392b"; MODEL = "#4f8471"; PAPER = "#ffffff"
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 8.5, "axes.edgecolor": RULE, "axes.labelcolor": INK2,
    "xtick.color": INK2, "ytick.color": INK, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": "#e3ece8", "grid.linewidth": 0.8, "savefig.dpi": 200, "svg.fonttype": "path",
})
ORDER = ["qwen3:0.6b", "qwen3:1.7b", "qwen3:4b", "qwen3:8b", "qwen3:14b", "llama3.1:8b", "mistral:7b", "gemma4:latest", "gemma3:12b", "phi4:14b"]
NAMES = {"qwen3:0.6b": "Qwen3 0.6B", "qwen3:1.7b": "Qwen3 1.7B", "qwen3:4b": "Qwen3 4B", "qwen3:8b": "Qwen3 8B", "qwen3:14b": "Qwen3 14B",
         "llama3.1:8b": "Llama 3.1 8B", "mistral:7b": "Mistral 7B", "gemma4:latest": "Gemma 4 8B", "gemma3:12b": "Gemma 3 12B", "phi4:14b": "Phi-4 14B"}
MODELS = [m for m in ORDER if m in D["models"]]
EXPS = D["experiments"]; LAB = D["labels"]


def row(m, e, surface="novel", mode="fast", persona="none"):
    for r in D["results"]:
        if r["model"] == m and r["exp"] == e and r["surface"] == surface and r["mode"] == mode and r["persona"] == persona:
            return r
    return None


def mean_abs_bq(m, surface="novel", mode="fast", persona="none"):
    v = [abs(row(m, e, surface, mode, persona)["bq"]) for e in EXPS if row(m, e, surface, mode, persona) and row(m, e, surface, mode, persona)["bq"] is not None]
    return float(np.mean(v)) if len(v) == len(EXPS) else None


def save(fig, name):
    fig.savefig(f"{OUT}/{name}.svg", bbox_inches="tight")
    fig.savefig(f"{OUT}/{name}.png", bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------- Fig 1: audit heatmap
def fig_heatmap(surface="novel", mode="fast", persona="none", name="fig1_audit"):
    ms = sorted(MODELS, key=lambda m: 9 if mean_abs_bq(m, surface, mode, persona) is None else mean_abs_bq(m, surface, mode, persona))
    def bq(m, e):
        r = row(m, e, surface, mode, persona)
        return np.nan if (r is None or r["bq"] is None) else r["bq"]   # 0.0 is a real value, not missing
    M = np.array([[bq(m, e) for e in EXPS] for m in ms], float)
    cmap = LinearSegmentedColormap.from_list("bq", ["#2f7a5f", "#f4f8f6", RED])
    fig, ax = plt.subplots(figsize=(7.2, 0.34 * len(ms) + 1.2))
    ax.grid(False)
    im = ax.imshow(np.clip(M, -1.5, 1.5), cmap=cmap, norm=TwoSlopeNorm(0, -1.5, 1.5), aspect="auto")
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            v = M[i, j]
            ax.text(j, i, "n/a" if np.isnan(v) else f"{v:.2f}", ha="center", va="center", fontsize=7.5,
                    color="white" if (not np.isnan(v) and abs(v) > 0.9) else INK)
    ax.set_xticks(range(len(EXPS)), [LAB[e].replace(" ", "\n", 1) for e in EXPS], fontsize=7.5)
    mb = lambda m: mean_abs_bq(m, surface, mode, persona)
    ax.set_yticks(range(len(ms)), [f"{NAMES[m]}   " + ("n/a" if mb(m) is None else f"{mb(m):.2f}") for m in ms])
    ax.xaxis.tick_top()
    for s in ax.spines.values(): s.set_visible(False)
    cb = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
    cb.set_label("Bias quotient (1 = human-level)", color=INK2)
    cb.outline.set_visible(False)
    save(fig, name)


# ---------------------------------------------------------------- Fig 2: each bias, per model, with CI
def fig_per_bias(name="fig2_per_bias"):
    fig, axes = plt.subplots(2, 4, figsize=(7.4, 4.9), sharey=True)
    ys = np.arange(len(MODELS))
    for k, e in enumerate(EXPS):
        ax = axes.flat[k]
        h = D["human"][e]["value"]
        for i, m in enumerate(MODELS):
            r = row(m, e)
            if not r or r["bias"] is None: continue
            lo, hi = r["ci_lo"], r["ci_hi"]
            if lo is not None: ax.plot([lo, hi], [i, i], color=MODEL, lw=1.6, solid_capstyle="round")
            ax.plot(r["bias"], i, "o", ms=4.5, color=MODEL, mec="white", mew=0.8)
        ax.axvline(0, color=INK2, lw=0.8, ls=(0, (2, 2)))
        ax.axvline(h, color=RED, lw=1.2)
        ax.set_title(LAB[e], fontsize=8.5, color=INK, loc="left")
        ax.tick_params(axis="x", labelsize=7)
    axes.flat[-1].axis("off")
    axes.flat[-1].text(0, 0.7, "Dot = model estimate\nBar = 95% bootstrap CI\nRed line = human effect\nDashed = no bias",
                       fontsize=7.5, color=INK2, transform=axes.flat[-1].transAxes, va="top")
    for ax in axes[:, 0]:
        ax.set_yticks(ys, [NAMES[m] for m in MODELS], fontsize=7)
    axes[0, 0].invert_yaxis()
    fig.tight_layout()
    save(fig, name)


# ---------------------------------------------------------------- Fig 3: scaling
def fig_scaling(name="fig3_scaling"):
    qs = [m for m in ["qwen3:0.6b", "qwen3:1.7b", "qwen3:4b", "qwen3:8b", "qwen3:14b"] if m in MODELS]
    x = [float(m.split(":")[1][:-1]) for m in qs]
    fig, ax = plt.subplots(figsize=(4.6, 2.6))
    for mode, style, lab in [("fast", dict(color=MODEL, ls="--", marker="o", mfc="white"), "Fast"), ("deliberate", dict(color=INK, marker="o"), "Thinks first")]:
        ax.plot(x, [mean_abs_bq(m, "novel", mode) for m in qs], lw=1.8, ms=5, label=lab, **style)
    ax.set_xscale("log"); ax.set_xticks(x, [f"{v:g}B" for v in x]); ax.minorticks_off()
    ax.axhline(1, color=RED, lw=1); ax.text(x[-1], 1.03, "human level", color=RED, ha="right", fontsize=7.5)
    ax.set_ylabel("Mean |bias quotient|"); ax.set_xlabel("Qwen3 model size (parameters)")
    ax.set_ylim(bottom=0); ax.legend(frameon=False, fontsize=7.5)
    save(fig, name)


# ---------------------------------------------------------------- Fig 4: paired comparisons
def fig_pairs(name="fig4_conditions"):
    comps = [
        ("Textbook vs. new wording", ("classic", "fast", "none"), ("novel", "fast", "none"), "Textbook", "New financial"),
        ("Fast vs. thinks first", ("novel", "fast", "none"), ("novel", "deliberate", "none"), "Fast", "Thinks first"),
        ("No persona vs. advisor", ("novel", "fast", "none"), ("novel", "fast", "advisor"), "No persona", "Advisor persona"),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(7.4, 3.2), sharey=True)
    for ax, (title, a, b, la, lb) in zip(axes, comps):
        for i, m in enumerate(MODELS):
            va, vb = mean_abs_bq(m, *a), mean_abs_bq(m, *b)
            if va is None or vb is None: continue
            ax.plot([va, vb], [i, i], color=MODEL, lw=1.6)
            ax.plot(va, i, "o", ms=5, mfc="white", mec=MODEL, mew=1.5)
            ax.plot(vb, i, "o", ms=5, color=MODEL, mec="white", mew=0.8)
        ax.axvline(1, color=RED, lw=1)
        ax.set_title(title, fontsize=8.5, loc="left", color=INK)
        ax.set_xlabel(f"○ {la}   ● {lb}", fontsize=7)
        ax.set_xlim(left=0)
    axes[0].set_yticks(range(len(MODELS)), [NAMES[m] for m in MODELS], fontsize=7)
    axes[0].invert_yaxis()
    fig.tight_layout()
    save(fig, name)


# ---------------------------------------------------------------- Fig 5: loss-aversion curves
def fig_loss_curves(name="fig5_loss_curves"):
    fig, ax = plt.subplots(figsize=(4.6, 2.8))
    for m in MODELS:
        r = row(m, "loss_aversion")
        if not r: continue
        c = r["parts"].get("accept_curve") or {}
        xs = sorted(int(k) for k in c)
        ax.plot(xs, [c[str(k)] if str(k) in c else c.get(k) for k in xs], color=MODEL, lw=1.2, alpha=0.75)
    ax.axvline(100, color=INK2, ls=(0, (2, 2)), lw=0.8); ax.text(104, 0.04, "break-even", fontsize=7, color=INK2)
    ax.axvline(225, color=RED, lw=1); ax.text(229, 0.04, "human λ = 2.25", fontsize=7, color=RED)
    ax.set_xscale("log"); ax.set_xticks([50, 100, 150, 200, 300, 400, 600], ["$50", "$100", "$150", "$200", "$300", "$400", "$600"]); ax.minorticks_off()
    ax.set_ylim(-0.03, 1.03); ax.set_xlabel("Win if heads (loss if tails = $100)"); ax.set_ylabel("Share accepting the bet")
    save(fig, name)


if __name__ == "__main__":
    fig_heatmap(); fig_heatmap("novel", "deliberate", "none", "fig1b_audit_deliberate"); fig_heatmap("classic", "fast", "none", "fig1c_audit_classic")
    fig_per_bias(); fig_scaling(); fig_pairs(); fig_loss_curves()
    print("figures written to", OUT)
