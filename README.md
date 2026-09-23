# Tails, You Lose

**Do AI language models inherit human money biases?** An original study by Daniel Yerushalmi.

Ten open-weight language models (0.6 to 14 billion parameters, from Alibaba, Meta, Mistral, Google and Microsoft) took seven classic behavioral-finance experiments: the framing effect, loss aversion, anchoring, the sunk-cost fallacy, the disposition effect, mental accounting and the certainty effect. That came to 31,500 independent decisions (31,494 usable), plus 8,100 in an exploratory variant, all run locally on one consumer GPU for $0 in API fees.

- **Interactive site:** https://tails-you-lose.vercel.app: take the same tests and see which model decides most like you (source in `site/`)
- **Paper:** [`paper/paper.pdf`](paper/paper.pdf)
- **Raw data:** every trial, with the model's raw output, in `data/trials.jsonl`

## Key findings

- **The average hides the story.** On new financial problems the models averaged a bias quotient of 0.59 (1.00 = as biased as people). Eight of ten never fell for the sunk-cost fallacy, and most sold the losing stock (the tax-smart move).
- **Anchoring is worse than in people.** Six of ten models were more anchored than humans by a number they were told was random when valuing a stock. Having the model write out the P/E arithmetic first fixed most of it.
- **Call it a trade, not a gamble, and they take the losing bet.** The same stake-$100-to-win-$50 bet was accepted 35% of the time as a coin flip and 81% as a brokerage trade. (Framing it as a friend's business, our first hypothesis, adds little: 89%.)
- **A "disciplined financial advisor" persona made models significantly more biased** (0.59 to 0.85; 8 of 10 models worse; Wilcoxon p = 0.01), mostly by turning them too cautious.
- **Thinking first trades one bias for another.** It cut anchoring (1.23 to 0.49) but strengthened the certainty effect (0.11 to 1.04).
- **Famous test problems are a poor guide** to behavior on new problems with the same structure, in both directions.

## Design in one paragraph

Every trial is a fresh conversation: the model sees exactly one version of one problem, just like a subject in a between-subjects human study. Answer options are shuffled on every trial, so a model's preference for "Option A" can't pose as a real preference. Each experiment exists twice, in its famous textbook wording and in a new financial scenario with the same structure. If a model is only rational on the textbook version, it memorized the answer. Models answered in two modes, **fast** (answer only) and **thinks first** (writes its reasoning before answering), and once more with a "CFA-certified financial advisor" persona. That gives 30 trials per cell at temperature 0.8, with structured JSON output enforced by Ollama's schema-constrained decoding.

**Bias quotient (BQ)** = the model's bias ÷ the human bias on the same measure. 0 means perfectly consistent, and 1 means exactly as biased as people in the classic studies. Confidence intervals are 95% bootstrap intervals.

## Reproduce

Requirements: [Ollama](https://ollama.com) and Python 3.11+ with `httpx pandas numpy scipy matplotlib`.

```bash
ollama pull qwen3:0.6b qwen3:1.7b qwen3:4b qwen3:8b qwen3:14b llama3.1:8b mistral:7b gemma3:12b phi4:14b
# gemma4:latest was also used
OLLAMA_NUM_PARALLEL=4 ollama serve
./run_all.sh                                   # resumable; about 3 hours on an RTX 5080
cd study && python analyze.py ../data/trials.jsonl ../data/summary.json
python figures.py ../data/summary.json ../paper/fig
```

Run the site with any static server from `site/`: `python -m http.server 3001`.

## Layout

```
study/experiments.py   every prompt (textbook + new financial versions)
study/run.py           trial generator + async runner (seeded, resumable)
study/analyze.py       bias metrics, bootstrap CIs, bias quotient -> summary.json
study/figures.py       paper figures
research/              verified human baselines and related work
paper/                 the paper (HTML source, PDF, figures)
site/                  the interactive site (static; Three.js + Rapier coins)
```

## Honest limitations

These are small open models, not frontier chat models. Human baselines come from the original published studies, which used different wording (the textbook versions). Thirty trials per cell gives wide intervals on some measures. The full list is in the paper.

Built with extensive AI assistance: Anthropic's Claude wrote much of the experiment code, analysis and site under the author's direction. The author chose the research direction and the business/finance framing, and is responsible for the final work.
