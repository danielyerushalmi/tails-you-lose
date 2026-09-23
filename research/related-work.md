# Related Work: AI Language Models and Behavioral Finance Biases

Verified research papers on LLMs exhibiting human-like cognitive and behavioral biases, particularly in economic decision-making and psychological reasoning tasks.

---

## Core Papers on LLM Behavioral Biases

### 1. Horton, John J. (2023)
**Title:** Large Language Models as Simulated Economic Agents: What Can We Learn from Homo Silicus?

**Authors:** John J. Horton, Apostolos Filippas, Benjamin S. Manning

**Year:** 2023 (revised February 2026)

**Venue:** NBER Working Paper No. w31122

**URL:** https://www.nber.org/papers/w31122

**Main Findings:** LLMs function as implicit computational models of human economic behavior ("Homo silicus"). When given economic scenarios with endowments, information, and preferences, they produce results qualitatively comparable to original human subject studies in behavioral economics experiments. Deviations often suggest productive research directions.

---

### 2. Binz, Marcel & Schulz, Eric (2023)
**Title:** Using cognitive psychology to understand GPT-3

**Authors:** Marcel Binz, Eric Schulz

**Year:** 2023

**Venue:** Proceedings of the National Academy of Sciences, 120(6):e2218523120

**URL:** https://www.pnas.org/doi/abs/10.1073/pnas.2218523120

**ArXiv:** https://arxiv.org/abs/2206.14576

**Main Findings:** GPT-3 demonstrates mixed cognitive capabilities: it performs well on vignette-based decision tasks and outperforms humans in multi-armed bandit tasks (showing signatures of model-based reinforcement learning), but is vulnerable to small task perturbations, lacks directed exploration, and fails at causal reasoning tasks.

---

### 3. Hagendorff, Thilo, Fabi, Sarah, & Kosinski, Michal (2023)
**Title:** Human-like intuitive behavior and reasoning biases emerged in large language models but disappeared in ChatGPT

**Authors:** Thilo Hagendorff, Sarah Fabi, Michal Kosinski

**Year:** 2023

**Venue:** Nature Computational Science, 3:833–838

**URL:** https://www.nature.com/articles/s43588-023-00527-x

**ArXiv:** https://arxiv.org/abs/2306.07622

**Main Findings:** Larger GPT models (especially GPT-3) increasingly display System 1-like cognitive errors and human-like reasoning biases in response to semantic illusions and cognitive reflection tests. However, ChatGPT (GPT-3.5/4) models learned to avoid these traps, responding correctly and outperforming humans. This accuracy persists even when chain-of-thought reasoning is prevented, suggesting the biases disappeared at a deeper algorithmic level.

---

### 4. Chen, Yiting, Liu, Tracy Xiao, Shan, You, & Zhong, Songfa (2023)
**Title:** The emergence of economic rationality of GPT

**Authors:** Yiting Chen, Tracy Xiao Liu, You Shan, Songfa Zhong

**Year:** 2023

**Venue:** Proceedings of the National Academy of Sciences, 120(51):e2316205120

**URL:** https://www.pnas.org/doi/10.1073/pnas.2316205120

**ArXiv:** https://arxiv.org/abs/2305.12763

**Main Findings:** GPT demonstrates high economic rationality when making budgetary decisions across risk, time, social, and food preference domains, with rationality scores exceeding those of human subjects. Rationality is robust to randomness and demographic factors but sensitive to language framing and contextual factors.

---

### 5. Macmillan-Scott, Olivia & Musolesi, Mirco (2024)
**Title:** (Ir)rationality and Cognitive Biases in Large Language Models

**Authors:** Olivia Macmillan-Scott, Mirco Musolesi

**Year:** 2024

**Venue:** Royal Society Open Science, 11(6):240255

**URL:** https://royalsocietypublishing.org/rsos/article/11/6/240255

**ArXiv:** https://arxiv.org/abs/2402.09193

**Main Findings:** Like humans, LLMs display irrationality in cognitive psychology tasks, but the nature of this irrationality differs fundamentally from human biases. Incorrect LLM responses often diverge from typical human cognitive error patterns, and models exhibit significant inconsistency—an additional layer of irrationality uncommon in human reasoning.

---

### 6. Suri, Gaurav, Slater, Lily R., Ziaee, Ali, & Nguyen, Morgan (2024)
**Title:** Do Large Language Models Show Decision Heuristics Similar to Humans? A Case Study Using GPT-3.5

**Authors:** Gaurav Suri, Lily R. Slater, Ali Ziaee, Morgan Nguyen

**Year:** 2024

**Venue:** Journal of Experimental Psychology: General, 153(4):1066–1075

**URL:** https://psycnet.apa.org/doiLanding?doi=10.1037%2Fxge0001547

**ArXiv:** https://arxiv.org/abs/2305.04400

**Main Findings:** Across four studies, ChatGPT exhibits four major human-like decision heuristics: anchoring (influenced by random numerical anchors), representativeness/availability (overestimating joint probabilities, influenced by anecdotes), framing effect (valuing items differently based on positive vs. negative description), and endowment effect (overvaluing owned items). Human participants showed equivalent effects in all studies.

---

## Behavioral Finance and Economic Biases

### 7. Ross, Jillian, Kim, Yoon, & Lo, Andrew W. (2024)
**Title:** LLM economicus? Mapping the Behavioral Biases of LLMs via Utility Theory

**Authors:** Jillian Ross, Yoon Kim, Andrew W. Lo

**Year:** 2024

**Venue:** COLM 2024

**URL:** https://openreview.net/forum?id=Rx3wC8sCTJ

**ArXiv:** https://arxiv.org/abs/2408.02784

**Main Findings:** LLMs demonstrate systematic economic biases including loss aversion and anchoring that lead to suboptimal decisions. Using utility theory to quantify these biases, the authors show that current LLMs fall "neither entirely human-like nor entirely economicus-like" and struggle to maintain consistent economic behavior across settings. Interventions like prompting can influence these biases.

---

### 8. Hu, Xiaoyu & Zhao, Jinman (2026)
**Title:** Fin-Bias: Comprehensive Evaluation for LLM Decision-Making under human bias in Finance Domain

**Authors:** Xiaoyu Hu, Jinman Zhao

**Year:** 2026

**Venue:** arXiv

**URL:** https://arxiv.org/abs/2605.09106

**Main Findings:** Benchmark study of 8,868 firm-specific analyst reports showing that LLMs tend to herd explicit bias in financial contexts. Models exhibit herding behavior when confronted with potentially biased analyst perspectives, though techniques have been developed to mitigate human opinion bias in model outputs.

---

### 9. Hashimoto, Ryuji, Takayanagi, Takehiro, Suzuki, Masahiro, & Izumi, Kiyoshi (2025)
**Title:** Agent-Based Simulation of a Financial Market with Large Language Models

**Authors:** Ryuji Hashimoto, Takehiro Takayanagi, Masahiro Suzuki, Kiyoshi Izumi

**Year:** 2025

**Venue:** arXiv (also in Springer proceedings)

**URL:** https://arxiv.org/abs/2510.12189

**Main Findings:** FCLAgent framework demonstrates that LLMs can emulate human-like trading decisions incorporating behavioral biases. Simulations show that LLM-based agents reproduce path-dependent market patterns (e.g., price declines near historical highs) that conventional agents cannot capture. Loss aversion reference points shift with market trajectories, enabling more realistic investor behavior modeling than traditional methods.

---

## Position Bias and Multiple-Choice Question Robustness

### 10. Pezeshkpour, Pouya & Hruschka, Estevam (2023)
**Title:** Large Language Models Sensitivity to The Order of Options in Multiple-Choice Questions

**Authors:** Pouya Pezeshkpour, Estevam Hruschka

**Year:** 2023

**Venue:** ACL: NAACL 2024 (Findings)

**ArXiv:** https://arxiv.org/abs/2308.11483

**Main Findings:** LLMs exhibit substantial sensitivity to answer option ordering in multiple-choice questions, with performance variations of 13–75% across benchmarks. Positional bias emerges when models are uncertain between top candidates; strategic placement of strong answers (first and last positions) amplifies bias, while adjacent placement mitigates it. Calibration approaches improved performance by up to 8 percentage points.

---

### 11. Zheng, Chujie, Zhou, Hao, Meng, Fandong, Zhou, Jie, & Huang, Minlie (2024)
**Title:** Large Language Models Are Not Robust Multiple Choice Selectors

**Authors:** Chujie Zheng, Hao Zhou, Fandong Meng, Jie Zhou, Minlie Huang

**Year:** 2024

**Venue:** ICLR 2024 (Spotlight)

**URL:** https://arxiv.org/abs/2309.03882

**Main Findings:** LLMs exhibit "selection bias"—they preferentially select specific option IDs (A/B/C/D) independent of content, stemming from token-level probability bias toward certain letters. Testing across 20 models and three benchmarks reveals this fundamental vulnerability. The authors propose PriDe, an inference-time debiasing method that estimates and corrects for this prior bias without labeled data.

---

## Classic Behavioral Economics Reference

### 12. Kahneman, Daniel (2011)
**Title:** Thinking, Fast and Slow

**Author:** Daniel Kahneman

**Year:** 2011

**Publisher:** Farrar, Straus and Giroux

**Main Concept:** Foundational work distinguishing System 1 (fast, intuitive, automatic) and System 2 (slow, deliberate, logical) thinking. Documents systematic human cognitive biases including anchoring, representativeness, availability heuristics, framing effects, and loss aversion—the psychological phenomena that form the basis for behavioral finance theories and many of the cognitive tasks used to evaluate LLMs in the above papers.

---

## Unverified/Not Found

### Data Contamination in Psychology Vignettes
**Search Status:** UNVERIFIED

No specific published paper found confirming that standard LLMs memorize and reproduce classic psychology problems (Linda problem, Asian disease problem) while failing on re-worded variants due to training data leakage. While general data contamination research exists (e.g., "Leak, Cheat, Repeat"), specific evidence tying it to classic behavioral economics vignettes remains unlocated in peer-reviewed venues as of this search (September 2026).

---

## Summary

**Total Verified Papers:** 12  
**Papers Specifically on Money/Finance Biases:** 4 (Papers 1, 4, 7, 8, 9)  
**Papers on Cognitive/Reasoning Biases:** 8 (Papers 2, 3, 5, 6)  
**Papers on Robustness/Position Bias:** 2 (Papers 10, 11)  
**Foundational Theory:** 1 (Paper 12)

All papers have been cross-referenced with primary sources (PNAS, Nature, arXiv, NBER, journal/conference websites) to confirm exact titles, authorship, publication venues, and main findings.
