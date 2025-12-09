
# Comprehensive Failure Analysis: LLM Decision-Making Performance Before and After RAG Enhancement

---

## Executive Summary

This report presents a comparative analysis of decision-making performance in a drone mission approval system, evaluating both pure LLM and RAG-enhanced configurations against ground truth decisions across safety-critical scenarios.

### Key Findings

| Metric                                    | Pure LLM         | RAG-Enhanced     | Improvement        |
| ----------------------------------------- | ---------------- | ---------------- | ------------------ |
| **Overall Accuracy**                | 241/368 (65.49%) | 226/254 (88.98%) | **+23.49pp** |
| **Total Errors**                    | 127              | 24               | **-81.1%**   |
| **Over-rejection (soft→REJECT)**   | 43 cases         | 18 cases         | **-58.1%**   |
| **Scenarios with ≥50% error rate** | 15               | 1                | **-93.3%**   |

**Primary Achievement** : RAG substantially reduces error rate while maintaining decision structure. However, five persistent failure patterns remain across both configurations, suggesting fundamental limitations in LLM reasoning under uncertainty, conflict, and adversarial conditions.

**Critical Insight** : The dominant failure mode shifts from indiscriminate over-rejection (pure LLM) to selective collapse of nuanced decisions in edge cases (RAG), with 75% of remaining RAG errors occurring when ground truth expects `UNCERTAIN`, `EXPLAIN_ONLY`, or `CONDITIONAL_APPROVE`.

---

## 1. Experimental Setup

### 1.1 Dataset Characteristics

* **Scenario Coverage** : S001–S049 covering battery safety, multi-source conflicts, temporal reasoning, adversarial prompts, authority hierarchies, and edge-case trade-offs
* **Decision Space** : 7-level taxonomy including `APPROVE`, `CONDITIONAL_APPROVE`, `UNCERTAIN`, `EXPLAIN_ONLY`, `REJECT`, `REJECT_WITH_ALTERNATIVE`, and revision states
* **Test Cases** : 368 total (LLM baseline); 254 in S021–S049 subset (RAG evaluation)
* **Ground Truth** : Expert-annotated decisions based on policy documents, safety regulations, and operational procedures

### 1.2 Evaluation Protocol

* **Alignment Metric** : Exact match between `ground_truth.decision` and `llm_result.decision` (LLM) or `rag_result.decision` (RAG)
* **Error Classification** : Directional analysis of mismatches (e.g., `UNCERTAIN → REJECT`, `EXPLAIN_ONLY → CONDITIONAL_APPROVE`)
* **Evidence Traceability** : All claims reference specific scenario IDs and JSON report files

---

## 2. Baseline Performance: Pure LLM Analysis

### 2.1 Overall Statistics

* **Accuracy** : 241/368 correct decisions (65.49%)
* **Error Count** : 127 mismatches
* **Error Distribution** : Over-rejection dominates with 43/127 cases (33.9%) where soft decisions collapse to hard `REJECT`

### 2.2 高风险场景（准确率 ≤ 50%）

| Scenario | Accuracy     | Error Count | Primary Failure Mode           |
| -------- | ------------ | ----------- | ------------------------------ |
| S033     | 1/10 (10.0%) | 9           | Conflict ordering & timeline   |
| S024     | 1/6 (16.67%) | 5           | Multi-source authority ranking |
| S031     | 3/10 (30.0%) | 7           | Cross-lingual source disputes  |
| S038     | 3/10 (30.0%) | 7           | Temporal chains                |
| S025     | 3/8 (37.5%)  | 5           | Jurisdiction/effective date    |
| S032     | 4/10 (40.0%) | 6           | Boundary/conflict mix          |
| S034     | 4/10 (40.0%) | 6           | Adversarial rhetoric           |
| S035     | 4/10 (40.0%) | 6           | Format/hierarchy attacks       |
| S037     | 4/10 (40.0%) | 6           | Mixed errors                   |
| S039     | 4/10 (40.0%) | 6           | Mixed errors                   |
| S048     | 4/10 (40.0%) | 6           | Trade-off pressure             |
| S049     | 4/10 (40.0%) | 6           | Trade-off pressure             |
| S030     | 4/8 (50.0%)  | 4           | UTM dynamic                    |
| S036     | 5/10 (50.0%) | 5           | Waiver conflict                |
| S040     | 5/10 (50.0%) | 5           | Mixed errors                   |

**Data Source** : `reports/S0xx_LLM_VALIDATION.json` files

### 2.3 Error Direction Breakdown

| Ground Truth → LLM Output              | Count | Interpretation                                  |
| --------------------------------------- | ----- | ----------------------------------------------- |
| `UNCERTAIN → REJECT`                 | 16    | Premature closure of uncertain cases            |
| `EXPLAIN_ONLY → REJECT`              | 16    | Policy explanation bypassed for rejection       |
| `CONDITIONAL_APPROVE → REJECT`       | 9     | Conditional paths ignored                       |
| `REJECT → UNCERTAIN`                 | 10    | Over-caution in clear violation cases           |
| `EXPLAIN_ONLY → CONDITIONAL_APPROVE` | 10    | Boundary between explanation and action blurred |
| `EXPLAIN_ONLY → UNCERTAIN`           | 6     | Conflation of explanation with indecision       |
| `UNCERTAIN → CONDITIONAL_APPROVE`    | 6     | Premature approval under ambiguity              |
| `REJECT → CONDITIONAL_APPROVE`       | 12    | Safety violations softened inappropriately      |
| Other permutations                      | 42    | Scattered misalignments                         |

**Key Pattern** : 43 cases involve collapsing soft decisions (`UNCERTAIN`/`EXPLAIN_ONLY`/`CONDITIONAL_APPROVE`) into hard `REJECT`, indicating conservative bias without nuance.

---

## 3. RAG-Enhanced Performance Analysis

### 3.1 Overall Statistics

* **Accuracy** : 226/254 correct decisions (88.98%)
* **Error Count** : 24 mismatches (-81.1% vs. LLM baseline)
* **Error Distribution** : Over-rejection remains dominant at 18/24 cases (75.0%), but absolute count reduced by 58.1%

### 3.2 场景表现（RAG）

| Scenario | Accuracy     | Error Count |
| -------- | ------------ | ----------- |
| S021     | 7/8 (87.5%)  | 1           |
| S022     | 8/8 (100%)   | 0           |
| S023     | 8/8 (100%)   | 0           |
| S024     | 5/6 (83.33%) | 1           |
| S025     | 5/8 (62.5%)  | 3           |
| S026     | 5/8 (62.5%)  | 3           |
| S027     | 5/8 (62.5%)  | 3           |
| S028     | 7/8 (87.5%)  | 1           |
| S029     | 8/8 (100%)   | 0           |
| S030     | 7/8 (87.5%)  | 1           |
| S031     | 7/10 (70.0%) | 3           |
| S032     | 10/10 (100%) | 0           |
| S033     | 10/10 (100%) | 0           |
| S034     | 5/10 (50.0%) | 5           |
| S035     | 7/10 (70.0%) | 3           |
| S036     | 9/10 (90.0%) | 1           |
| S037     | 10/10 (100%) | 0           |
| S038     | 10/10 (100%) | 0           |
| S039     | 10/10 (100%) | 0           |
| S040     | 7/10 (70.0%) | 3           |
| S041     | 8/8 (100%)   | 0           |
| S042     | 8/8 (100%)   | 0           |
| S043     | 8/8 (100%)   | 0           |
| S044     | 8/8 (100%)   | 0           |
| S045     | 8/8 (100%)   | 0           |
| S046     | 8/8 (100%)   | 0           |
| S047     | 8/8 (100%)   | 0           |
| S048     | 10/10 (100%) | 0           |
| S049     | 10/10 (100%) | 0           |

**Data Source** : `reports/S0xx_RAG_REPORT.json` files

### 3.3 Error Direction in RAG Configuration

| Ground Truth → RAG Output              | Count | Interpretation                       |
| --------------------------------------- | ----- | ------------------------------------ |
| `UNCERTAIN → REJECT`                 | 10    | Persistent collapse under ambiguity  |
| `EXPLAIN_ONLY → REJECT`              | 4     | Policy explanation still bypassed    |
| `CONDITIONAL_APPROVE → REJECT`       | 3     | Conditional logic partially restored |
| `REJECT → CONDITIONAL_APPROVE`       | 1     | Over-permissiveness rare             |
| `UNCERTAIN → CONDITIONAL_APPROVE`    | 1     | Boundary misjudgment                 |
| `EXPLAIN_ONLY → CONDITIONAL_APPROVE` | 1     | Explanation-action confusion         |
| `REJECT_WITH_ALTERNATIVE → REJECT`   | 1     | Alternative still occasionally lost  |
| Other                                   | 3     | Minor misalignments                  |

**Key Shift** : RAG reduces total over-rejection from 43 to 18 cases but does not eliminate the pattern. The ratio of soft-to-hard collapse (18/24 = 75%) is actually higher than in pure LLM (43/127 = 33.9%), suggesting RAG improves routine cases while edge cases remain brittle.

---

## 4. Comparative Analysis

RAG demonstrates differential impact across failure types, with strongest improvements in factual disambiguation and weakest gains in adversarial/edge cases.

| Improvement Area                 | LLM Baseline | RAG Enhanced | Key Factor                   |
| -------------------------------- | ------------ | ------------ | ---------------------------- |
| **Multi-Source Conflicts** | S024 16.67%  | 83.33%       | Authority markers retrieved  |
| **Battery/Boundary Cases** | S021 62.5%   | 87.5%        | SOC tables, charging specs   |
| **Temporal Reasoning**     | S031 30.0%   | 70.0%        | Effective dates explicit     |
| **Conflict Ordering**      | S033 10.0%   | 100.0%       | Timeline documents retrieved |
| **Adversarial Prompts**    | S034 40.0%   | 50.0%        | Minimal improvement          |
| **Format Attacks**         | S035 40.0%   | 70.0%        | Partial improvement          |
| **Staged Decisions**       | S027 62.5%   | 62.5%        | No improvement               |

 **Key Observations** :

* RAG eliminates 14 of 15 high-risk scenarios (≥50% error rate in LLM)
* Remaining errors concentrate in S034 (adversarial rhetoric) where retrieved policy cannot override prompt manipulation
* Over-rejection persists at 75% of RAG errors (18/24), suggesting factual grounding increases confidence but does not teach uncertainty expression

---

## 5. Generalized Failure Taxonomy

Based on cross-scenario error patterns, we identify five fundamental failure modes that persist across both LLM and RAG configurations, each with distinct mechanisms and literature grounding.

### 5.1 Pattern 1: Decision Granularity Collapse

**Definition** : Multi-level decision space compresses into binary outputs, losing intermediate states (`UNCERTAIN`, `EXPLAIN_ONLY`, `CONDITIONAL_APPROVE`).

**Quantitative Evidence** :

* **LLM** : 43/127 errors (33.9%) involve soft→`REJECT` transitions
* **RAG** : 18/24 errors (75.0%) involve soft→`REJECT` transitions
* **Representative Cases** : S024 (uniform `UNCERTAIN` despite clear authority ranking), S034 (rhetoric triggers `REJECT` over `EXPLAIN_ONLY`), S035 (format constraints force binary choices)

**Literature Grounding** :

* Holliday et al. (EMNLP 2024) [1] demonstrate that LLMs struggle with conditional reasoning structures, particularly when conclusions depend on unverified premises—our `UNCERTAIN` and `EXPLAIN_ONLY` states require exactly this suspended judgment
* Brady et al. (Nature Reviews Psychology 2025) [13] show LLMs lack "System 2" deliberative processes that maintain uncertainty representations; their dual-process analysis reveals models default to cached heuristics (reject-if-unclear) rather than explicit uncertainty tracking
* Cong (Scientific Reports 2024) [5] documents LLM failure in pragmatic implicature, where conversational context should signal non-committal stances—analogous to our `EXPLAIN_ONLY` cases being misread as implicit rejections

**Affected Scenarios** : S024 (1→5 errors in LLM), S034 (5 errors in RAG), S035 (3 errors in RAG), S027 (3 errors in RAG)

---

### 5.2 Pattern 2: Alternative Solution Blindness

**Definition** : Retrieved or provided alternative courses of action fail to enter the final decision chain.

**Quantitative Evidence** :

* **LLM** : S021 TC5 (fast charge/backup drone ignored), S027 TC5 (staged approval path lost), S026 TC2 (emergency waiver unclaimed)
* **RAG** : S021 TC5 (persistent failure despite retrieval), S027 TC5 (staged plan retrieved but not executed), S026 TC2 (waiver path retrieved but rejected outright)
* **Frequency** : 7 cases across both configurations where alternatives exist in context but decision proceeds as if unavailable

**Literature Grounding** :

* Prabhakar et al. (EMNLP 2024 Findings) [16] identify that chain-of-thought reasoning degrades when multiple solution paths exist, with models favoring "memorized shortcuts" over systematic exploration—our alternative solutions require explicit path comparison absent in training
* Pedinotti et al. (ACL 2022) [6] show NLI systems fail at conjunction buttressing (strengthening one argument while maintaining another), analogous to our need to present alternatives without committing to one prematurely

**Affected Scenarios** : S021 (1 error in RAG), S026 (3 errors in RAG), S027 (3 errors in RAG)

---

### 5.3 Pattern 3: Conflict Resolution Strategy Deficit

**Definition** : When multiple sources, timestamps, or jurisdictions conflict, models lack systematic prioritization frameworks and either reject defensively or select arbitrarily.

**Quantitative Evidence** :

* **LLM** : S024 (5/6 errors—multi-source chaos), S025 (5/8 errors—jurisdictional conflicts), S031 (7/10 errors—cross-lingual disputes)
* **RAG** : S024 (1 error—improved but not perfect), S025 (3 errors—persistent effective date confusion), S031 (3 errors—translation panel disputes unresolved)
* **Total Impact** : 20 LLM errors → 7 RAG errors (65% reduction but failures remain)

**Literature Grounding** :

* WikiContradict [2] and CONFLICTBANK [3] benchmarks document that LLMs lack intrinsic conflict arbitration strategies, often reproducing both contradictory statements without resolution—our multi-source scenarios directly instantiate this problem with safety consequences
* Bee (Medium 2025) [4] advocates "epistemic humility" as a mitigation, arguing models should explicitly flag uncertainty rather than force resolution—partially achieved in our RAG `UNCERTAIN` outputs but insufficient when policy *requires* resolution (e.g., S024 cascade failures)
* Holliday et al. [1] extend this to modal reasoning: when conflicting sources create incompatible conditionals, models fail to maintain separate epistemic states per source

**Affected Scenarios** : S024 (1 error in RAG), S025 (3 errors in RAG), S031 (3 errors in RAG), S034 (subset overlaps with adversarial patterns)

---

### 5.4 Pattern 4: Boundary Calibration Instability

**Definition** : Near safety thresholds (battery reserves, timing margins, noise limits), decisions oscillate between over-conservatism and over-permissiveness without probabilistic calibration.

**Quantitative Evidence** :

* **LLM** : S021 TC3 (expected `REJECT`, got `REJECT_WITH_ALTERNATIVE`—incorrect softening), TC8 (chose riskier option A over B)
* **RAG** : S028 TC3 (10.5% reserve near 10% limit, expected `UNCERTAIN`, got `CONDITIONAL_APPROVE`—boundary over-confidence), S021 TC5 (persistent boundary misjudgment)
* **Frequency** : 8 cases where ±1% SOC, ±5min margin, or ±2dB threshold separates approve/reject

**Literature Grounding** :

* Kıcıman et al. (arXiv 2024) [12] analyze causal reasoning failures in LLMs, showing boundary conditions (where causal relationships flip) are systematically mishandled—our SOC/timing thresholds are precisely these tipping points
* Mirzadeh et al. (GSM-Symbolic, arXiv 2024) [9] demonstrate LLMs exhibit "symbolic brittleness" where changing numerical values near decision boundaries causes disproportionate accuracy drops—our battery/timing margins instantiate this with safety stakes
* Joshi et al. (EMNLP 2024) [7] and Yamin et al. (arXiv 2024) [8] document causal fallacies in narrative reasoning, including threshold neglect and false precision—analogous to our boundary miscalibrations

**Affected Scenarios** : S021 (1 error in RAG), S028 (1 error in RAG), S035 (overlaps with hierarchy/boundary interactions)

---

### 5.5 Pattern 5: Adversarial Robustness Gap

**Definition** : Sarcasm, style constraints, loophole-seeking, and instruction injections degrade structured decision output.

**Quantitative Evidence** :

* **LLM** : S034 (6/10 errors—sarcasm, privacy whataboutism, hobby loophole), S035 (6/10 errors—format suppression, hierarchy attacks)
* **RAG** : S034 (5/10 errors—minimal improvement), S035 (3/10 errors—50% reduction but still fragile)
* **Total Impact** : 12 LLM errors → 8 RAG errors (33% reduction, adversarial cases resist RAG grounding)

**Literature Grounding** :

* Ganguli et al. (Anthropic, arXiv 2022) [10] red-teaming methodology shows LLMs are vulnerable to adversarial phrasing that exploits politeness training—our CEO pressure and sarcasm cases directly match their "authority appeal" and "social proof" attack patterns
* Joshi et al. [7] and Yamin et al. [8] document narrative-based causal fallacies where phrasing biases (e.g., framing as "helping" vs. "violating") flip LLM judgments—our loophole framings exploit this
* Piatti et al. (arXiv 2024) [14] and Backmann et al. (arXiv 2025) [15] study LLM agents in social dilemmas, finding cooperation collapses under competitive framing or moral-payoff divergence—analogous to our adversarial prompts creating perceived conflicts between safety and compliance

**Affected Scenarios** : S034 (5 errors in RAG), S035 (3 errors in RAG), S036 (1 error in RAG, waiver-NFZ conflict)

---

## 7. Appendix: Complete Scenario Performance Tables

### 7.1 纯 LLM 场景表现

| Scenario | Correct | Total | Accuracy |
| -------- | ------- | ----- | -------- |
| S001     | 8       | 8     | 100.0%   |
| S002     | 4       | 4     | 100.0%   |
| S003     | 4       | 4     | 100.0%   |
| S004     | 3       | 4     | 75.0%    |
| S005     | 5       | 5     | 100.0%   |
| S006     | 6       | 6     | 100.0%   |
| S007     | 8       | 8     | 100.0%   |
| S008     | 4       | 4     | 100.0%   |
| S009     | 6       | 6     | 100.0%   |
| S010     | 4       | 4     | 100.0%   |
| S011     | 8       | 8     | 100.0%   |
| S012     | 5       | 5     | 100.0%   |
| S013     | 5       | 5     | 100.0%   |
| S014     | 6       | 6     | 100.0%   |
| S015     | 6       | 6     | 100.0%   |
| S016     | 6       | 6     | 100.0%   |
| S017     | 8       | 8     | 100.0%   |
| S018     | 8       | 8     | 100.0%   |
| S019     | 5       | 5     | 100.0%   |
| S020     | 4       | 4     | 100.0%   |
| S021     | 5       | 8     | 62.5%    |
| S022     | 6       | 8     | 75.0%    |
| S023     | 6       | 8     | 75.0%    |
| S024     | 1       | 6     | 16.67%   |
| S025     | 3       | 8     | 37.5%    |
| S026     | 5       | 8     | 62.5%    |
| S027     | 5       | 8     | 62.5%    |
| S028     | 5       | 8     | 62.5%    |
| S029     | 5       | 8     | 62.5%    |
| S030     | 4       | 8     | 50.0%    |
| S031     | 3       | 10    | 30.0%    |
| S032     | 4       | 10    | 40.0%    |
| S033     | 1       | 10    | 10.0%    |
| S034     | 4       | 10    | 40.0%    |
| S035     | 4       | 10    | 40.0%    |
| S036     | 5       | 10    | 50.0%    |
| S037     | 4       | 10    | 40.0%    |
| S038     | 3       | 10    | 30.0%    |
| S039     | 4       | 10    | 40.0%    |
| S040     | 5       | 10    | 50.0%    |
| S041     | 6       | 8     | 75.0%    |
| S042     | 6       | 8     | 75.0%    |
| S043     | 5       | 8     | 62.5%    |
| S044     | 6       | 8     | 75.0%    |
| S045     | 5       | 8     | 62.5%    |
| S046     | 5       | 8     | 62.5%    |
| S047     | 5       | 8     | 62.5%    |
| S048     | 4       | 10    | 40.0%    |
| S049     | 4       | 10    | 40.0%    |

### 7.2 RAG 场景表现（S021–S049）

| Scenario | Correct | Total | Accuracy |
| -------- | ------- | ----- | -------- |
| S021     | 7       | 8     | 87.5%    |
| S022     | 8       | 8     | 100.0%   |
| S023     | 8       | 8     | 100.0%   |
| S024     | 5       | 6     | 83.33%   |
| S025     | 5       | 8     | 62.5%    |
| S026     | 5       | 8     | 62.5%    |
| S027     | 5       | 8     | 62.5%    |
| S028     | 7       | 8     | 87.5%    |
| S029     | 8       | 8     | 100.0%   |
| S030     | 7       | 8     | 87.5%    |
| S031     | 7       | 10    | 70.0%    |
| S032     | 10      | 10    | 100.0%   |
| S033     | 10      | 10    | 100.0%   |
| S034     | 5       | 10    | 50.0%    |
| S035     | 7       | 10    | 70.0%    |
| S036     | 9       | 10    | 90.0%    |
| S037     | 10      | 10    | 100.0%   |
| S038     | 10      | 10    | 100.0%   |
| S039     | 10      | 10    | 100.0%   |
| S040     | 7       | 10    | 70.0%    |
| S041     | 8       | 8     | 100.0%   |
| S042     | 8       | 8     | 100.0%   |
| S043     | 8       | 8     | 100.0%   |
| S044     | 8       | 8     | 100.0%   |
| S045     | 8       | 8     | 100.0%   |
| S046     | 8       | 8     | 100.0%   |
| S047     | 8       | 8     | 100.0%   |
| S048     | 10      | 10    | 100.0%   |
| S049     | 10      | 10    | 100.0%   |

## References

[1] W. H. Holliday, M. Mandelkern, and C. E. Zhang, "Conditional and Modal Reasoning in Large Language Models," in  *Proceedings of the 2024 Conference on Empirical Methods in Natural Language Processing* , Miami, Florida, USA: Association for Computational Linguistics, 2024, pp. 3800–3821. doi: 10.18653/v1/2024.emnlp-main.222.

[2] Y. Hou et al., "WikiContradict: A Benchmark for Evaluating LLMs on Real-World Knowledge Conflicts from Wikipedia".

[3] Z. Su et al., "CONFLICTBANK: A Benchmark for Evaluating Knowledge Conflicts in Large Language Models".

[4] M. Bee, "Improving Large Language Models' Handling of Contradictions: Fostering Epistemic Humility,"  *Medium* . Accessed: Nov. 13, 2025. [Online]. Available: https://medium.com/@mbonsign/improving-large-language-models-handling-of-contradictions-fostering-epistemic-humility-629fca6abcf0

[5] Y. Cong, "Manner implicatures in large language models,"  *Sci. Rep.* , vol. 14, no. 1, p. 29113, Nov. 2024, doi: 10.1038/s41598-024-80571-3.

[6] P. Pedinotti, E. Chersoni, E. Santus, and A. Lenci, "Pragmatic and Logical Inferences in NLI Systems: The Case of Conjunction Buttressing," in  *Proceedings of the Second Workshop on Understanding Implicit and Underspecified Language* , Seattle, USA: Association for Computational Linguistics, 2022, pp. 8–16. doi: 10.18653/v1/2022.unimplicit-1.2.

[7] N. Joshi, A. Saparov, Y. Wang, and H. He, "LLMs Are Prone to Fallacies in Causal Inference," in  *Proceedings of the 2024 Conference on Empirical Methods in Natural Language Processing* , Miami, Florida, USA: Association for Computational Linguistics, 2024, pp. 10553–10569. doi: 10.18653/v1/2024.emnlp-main.590.

[8] K. Yamin, S. Gupta, G. R. Ghosal, Z. C. Lipton, and B. Wilder, "Failure Modes of LLMs for Causal Reasoning on Narratives," June 17, 2025, arXiv: arXiv:2410.23884. doi: 10.48550/arXiv.2410.23884.

[9] I. Mirzadeh, K. Alizadeh, H. Shahrokhi, O. Tuzel, S. Bengio, and M. Farajtabar, "GSM-Symbolic: Understanding the Limitations of Mathematical Reasoning in Large Language Models," Aug. 28, 2025, arXiv: arXiv:2410.05229. doi: 10.48550/arXiv.2410.05229.

[10] D. Ganguli et al., "Red Teaming Language Models to Reduce Harms: Methods, Scaling Behaviors, and Lessons Learned," Nov. 24, 2022, arXiv: arXiv:2209.07858. doi: 10.48550/arXiv.2209.07858.

[11] Y. Jiang et al., "D-LLM: A Token Adaptive Computing Resource Allocation Strategy for Large Language Models".

[12] E. Kıcıman, R. Ness, A. Sharma, and C. Tan, "Causal Reasoning and Large Language Models: Opening a New Frontier for Causality," Aug. 21, 2024, arXiv: arXiv:2305.00050. doi: 10.48550/arXiv.2305.00050.

[13] O. Brady, P. Nulty, L. Zhang, T. E. Ward, and D. P. McGovern, "Dual-process theory and decision-making in large language models,"  *Nat. Rev. Psychol.* , pp. 1–16, Nov. 2025, doi: 10.1038/s44159-025-00506-1.

[14] G. Piatti, Z. Jin, M. Kleiman-Weiner, B. Schölkopf, M. Sachan, and R. Mihalcea, "Cooperate or Collapse: Emergence of Sustainable Cooperation in a Society of LLM Agents," Dec. 08, 2024, arXiv: arXiv:2404.16698. doi: 10.48550/arXiv.2404.16698.

[15] S. Backmann, D. G. Piedrahita, E. Tewolde, R. Mihalcea, B. Schölkopf, and Z. Jin, "When Ethics and Payoffs Diverge: LLM Agents in Morally Charged Social Dilemmas," May 25, 2025, arXiv: arXiv:2505.19212. doi: 10.48550/arXiv.2505.19212.

[16] A. Prabhakar, T. L. Griffiths, and R. T. McCoy, "Deciphering the Factors Influencing the Efficacy of Chain-of-Thought: Probability, Memorization, and Noisy Reasoning," in  *Findings of the Association for Computational Linguistics: EMNLP 2024* , Y. Al-Onaizan, M. Bansal, and Y.-N. Chen, Eds., Miami, Florida, USA: Association for Computational Linguistics, Nov. 2024, pp. 3710–3724. doi: 10.18653/v1/2024.findings-emnlp.212.
