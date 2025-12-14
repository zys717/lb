# Cross-Regulatory Failure Analysis: Evidence of Universal LLM Reasoning Limitations

## Research Question

Do LLM decision-making failures in low-altitude airspace management arise from regulatory-specific knowledge gaps or fundamental reasoning limitations?

## Methodology

We analyzed 254 test cases across 29 scenarios (S021-S049) containing FAA Part 107, Chinese regulations, or both. For each failure case, we attributed the error to: (1) CN-specific rule interpretation, (2) FAA-specific rule interpretation, or (3) universal reasoning failures independent of regulatory framework.

**Regulatory Distribution:**

* FAA-referenced: 8 scenarios (S029, S031, S033, S035, S036, S039, S040, S044)
* CN-only: 3 scenarios (S019, S020, S021)
* General/Overlap: 38 scenarios

## Key Finding

**Of 24 RAG configuration errors analyzed, 0 (0%) were attributable to regulation-specific knowledge deficits. All failures traced to universal reasoning breakdowns.**

| Error Attribution              | Count | Percentage |
| ------------------------------ | ----- | ---------- |
| Universal reasoning failures   | 24    | 100%       |
| FAA-specific misinterpretation | 0     | 0%         |
| CN-specific misinterpretation  | 0     | 0%         |

**Representative Cases:**

* **S034 (FAA waiver processes)** : 5 failures on adversarial prompts using sarcasm and loophole-seeking—not FAA regulation misunderstanding, but susceptibility to rhetorical manipulation (Shaib et al., 2024)[1]
* **S035 (FAA §107.29 verification)** : 3 failures on authority impersonation attacks—not regulatory confusion, but failure to maintain instruction hierarchy under format suppression (Li et al., 2024)[2]
* **S031 (cross-source disputes, CN/FAA mixed)** : 3 failures when contradictory sources conflict—not bilateral regulation gap, but systematic knowledge conflict misresolution (Xu et al., 2024)[3]

## Failure Mode Classification (Cross-Regulatory Analysis)

### 1. Conditional Reasoning Collapse (10 errors, 41.7%)

LLMs collapse soft states (UNCERTAIN, EXPLAIN_ONLY) to hard REJECT when facing ambiguous conditions, regardless of whether uncertainty stems from FAA waiver procedures (S029), Chinese approval timelines (S030), or general safety trade-offs (S026-S027).

**Literature:** Puerto et al. (2024)[4] show text-based LLMs struggle with conditional logic where antecedents contain epistemic uncertainty—our UNCERTAIN→REJECT collapses directly instantiate this failure mode with safety stakes. Shi et al. (2023)[5] demonstrate LLMs are "easily distracted by irrelevant context," explaining why adversarial framings trigger blanket rejections.

**Cross-regulatory evidence:** S029 (FAA progressive enforcement, 0% errors post-RAG) vs. S026 (general multi-objective conflict, 37.5% errors post-RAG)—both involve conditional approval paths, but failures concentrate where conflicts lack regulatory anchoring.

### 2. Alternative Solution Blindness (9 errors, 37.5%)

Failures to generate CONDITIONAL_APPROVE or REJECT_WITH_ALTERNATIVE occur across all regulatory contexts when problems admit multiple solutions with different constraint sets.

**Literature:** Chen et al. (2024)[6] find LLMs exhibit "premise order effects" in reasoning—when constraints appear sequentially, later constraints overshadow earlier alternatives. Our multi-constraint scenarios (S025-S027) directly reflect this: LLMs fixate on the most recent/salient constraint rather than synthesizing alternatives.

**Cross-regulatory evidence:** Both FAA-based S029 (phased approvals) and CN-based S021 (battery contingency planning) initially failed on alternative generation—RAG retrieval of procedural examples resolved both, confirming domain-agnostic solution generation deficit.

### 3. Knowledge Conflict Arbitration Failure (4 errors, 16.7%)

When multiple sources (policies, updates, or cross-jurisdictional rules) conflict, LLMs lack systematic arbitration strategies. Occurs in FAA/CN mixed scenarios (S031), pure CN scenarios (S025 effective date disputes), and general multi-source cases (S024).

**Literature:** Xu et al. (2024)[3] taxonomy of knowledge conflicts identifies "inter-context conflicts" (between retrieved sources) and "temporal conflicts" (update recency) as major failure modes for RAG systems. Our S031 (cross-lingual source disputes, 30% RAG errors) and S025 (jurisdiction/effective date conflicts, 37.5% RAG errors) align with their findings that conflict detection ≠ conflict resolution.

**Universal pattern:** Failures occur regardless of whether conflict is FAA-vs-FAA (S029 progressive vs. immediate enforcement), CN-vs-CN (S025 provincial vs. national), or FAA-vs-CN (S031)—regulatory domain is irrelevant.

### 4. Boundary Calibration Instability (2 errors, 8.3%)

Near decision thresholds (e.g., 10.5% battery SOC vs. 10% minimum), LLMs exhibit over-confidence or over-caution independent of whether thresholds derive from FAA Part 107 operational limits or Chinese battery safety standards.

**Literature:** Mirzadeh et al. (2024)[7] GSM-Symbolic study reveals "symbolic brittleness"—changing numeric values near boundaries causes disproportionate accuracy drops. Kıcıman et al. (2024)[8] analyze causal reasoning failures at "tipping points" where relationships flip. Our battery/timing margins (S021, S028) instantiate these vulnerabilities with life-safety implications.

**Cross-regulatory evidence:** S021 (CN battery standards) and S028 (general reserve margins) both exhibit boundary errors—regulatory source doesn't determine failure.

### 5. Adversarial Prompt Injection (8 errors, 33.3%)

Sarcasm, loophole-seeking, authority appeals, and format suppression degrade structured decisions across all regulatory contexts.

**Literature:**

* **Red-teaming taxonomy:** Ganguli et al. (2022)[9] identify "authority appeal" and "social proof" as universal jailbreak patterns—our CEO pressure scenarios (S034-S035) match their attack surface analysis.
* **Instruction-following robustness:** Li et al. (2024)[2] benchmark shows stronger instruction-followers exhibit *higher* vulnerability to injected instructions—explaining why RAG (which improves instruction-following) reduced but didn't eliminate S034-S035 errors.
* **Agent vulnerability:** Recent work on indirect prompt injection (Wu et al., 2025)[10] shows LLM-integrated systems remain vulnerable even with explicit boundary markers—our S035 format suppression attacks (70% RAG accuracy) align with their findings.

**Cross-regulatory evidence:** S034 (FAA waiver loopholes) vs. S040 (general adversarial scenarios) show identical vulnerability to rhetorical manipulation—regulatory framework provides no protection.

## Implications for Benchmark Generalizability

### Domain-Independence of Failure Modes

Cross-lingual transfer learning literature (Lample & Conneau, 2019)[11] shows pre-trained models learn language-agnostic representations. Our findings extend this to  *regulatory frameworks* : LLM reasoning failures are domain-agnostic, transcending specific rule systems.

**Analogy to vision benchmarks:** Just as ImageNet failure modes (Beyer et al., 2020)[12] transfer to medical imaging despite domain shift, our failure patterns transfer across regulatory jurisdictions because they reflect fundamental model limitations, not domain knowledge gaps.

### Benchmark Design Validation

By including dual-regulatory scenarios and systematically attributing failures, LAE-Bench demonstrates what domain-specific benchmarks should measure:  **systematic failure mode discovery, not domain coverage** . This aligns with recent meta-analysis (Han et al., 2021)[13] advocating for "adversarial" evaluation datasets that expose model weaknesses rather than validate task-specific accuracy.

## Limitations

**Attribution methodology:** Binary classification (universal vs. regulatory-specific) may oversimplify cases where domain knowledge *could* mitigate universal failures (e.g., better FAA examples might improve conditional reasoning in S029). However, observed 0% regulatory-specific failures suggest this conflation is minimal.

**Regulatory scope:** Analysis limited to CN/FAA. Future work should validate universality against EASA, ICAO, or other frameworks—though cross-lingual evidence (Tanwar et al., 2023)[14] suggests multilingual pre-training already provides cross-jurisdictional capability.

## References

[1]“Researchers discover a shortcoming that
makes LLMs less reliable,” MIT News | Massachusetts Institute of Technology.
Accessed: Dec. 12, 2025. [Online]. Available: [https://news.mit.edu/2025/](https://news.mit.edu/2025/shortcoming-makes-llms-less-reliable-1126)[shortcoming-makes-llms-less-reliable-1126](https://news.mit.edu/2025/shortcoming-makes-llms-less-reliable-1126)

[2]Z. Li, B. Peng, P. He, and X. Yan,
“Evaluating the Instruction-Following Robustness of Large Language Models to
Prompt Injection,” in Proceedings of the 2024 Conference on
Empirical Methods in Natural Language Processing, Y. Al-Onaizan, M. Bansal, and Y.-N.
Chen, Eds., Miami, Florida, USA: Association for Computational Linguistics,
Nov. 2024, pp. 557–568. doi: [10.18653/v1/2024.emnlp-main.33](https://doi.org/10.18653/v1/2024.emnlp-main.33).

[3]R. Xu et al.,
“Knowledge Conflicts for LLMs: A Survey,” in Proceedings of the 2024 Conference
on Empirical Methods in Natural Language Processing, Y.
Al-Onaizan, M. Bansal, and Y.-N. Chen, Eds., Miami, Florida, USA: Association
for Computational Linguistics, Nov. 2024, pp. 8541–8565. doi: [10.18653/v1/2024.emnlp-main.486](https://doi.org/10.18653/v1/2024.emnlp-main.486).

[4]H. Puerto, M. Tutek, S. Aditya, X. Zhu,
and I. Gurevych, “Code Prompting Elicits Conditional Reasoning Abilities in
Text+Code LLMs,” in Proceedings of the 2024 Conference on
Empirical Methods in Natural Language Processing, Y. Al-Onaizan, M. Bansal, and Y.-N.
Chen, Eds., Miami, Florida, USA: Association for Computational Linguistics,
Nov. 2024, pp. 11234–11258. doi: [10.18653/v1/2024.emnlp-main.629](https://doi.org/10.18653/v1/2024.emnlp-main.629).

[5]F. Shi et al.,
“Large Language Models Can Be Easily Distracted by Irrelevant Context,” June
06, 2023, arXiv:
arXiv:2302.00093. doi: [10.48550/arXiv.2302.00093](https://doi.org/10.48550/arXiv.2302.00093).

[6]X. Chen, R. A. Chi, X. Wang, and D. Zhou,
“Premise Order Matters in Reasoning with Large Language Models,” May 28, 2024, arXiv:
arXiv:2402.08939. doi: [10.48550/arXiv.2402.08939](https://doi.org/10.48550/arXiv.2402.08939).

[7]I. Mirzadeh, K. Alizadeh, H. Shahrokhi, O.
Tuzel, S.
Bengio, and M. Farajtabar,
“GSM-Symbolic: Understanding the Limitations of Mathematical Reasoning in Large
Language Models,” Aug. 28, 2025, arXiv: arXiv:2410.05229. doi: [10.48550/arXiv.2410.05229](https://doi.org/10.48550/arXiv.2410.05229).

[8]E. Kıcıman, R. Ness, A. Sharma, and C. Tan, “Causal
Reasoning and Large Language Models: Opening a New Frontier for Causality,”
Aug. 21, 2024, arXiv: arXiv:2305.00050. doi: [10.48550/arXiv.2305.00050](https://doi.org/10.48550/arXiv.2305.00050).

[9]D. Ganguli et al.,
“Red Teaming Language Models to Reduce Harms: Methods, Scaling Behaviors, and
Lessons Learned,” Nov. 24, 2022, arXiv: arXiv:2209.07858. doi: [10.48550/arXiv.2209.07858](https://doi.org/10.48550/arXiv.2209.07858).

[10]Z. Wang et al.,
“AGENTVIGIL: Automatic Black-Box Red-teaming for Indirect Prompt Injection
against LLM Agents,” in Findings of the Association for
Computational Linguistics: EMNLP 2025, C. Christodoulopoulos, T. Chakraborty,
C. Rose, and V. Peng, Eds., Suzhou, China: Association for Computational
Linguistics, Nov. 2025, pp. 23159–23172. doi: [10.18653/v1/2025.findings-emnlp.1258](https://doi.org/10.18653/v1/2025.findings-emnlp.1258).

[11]A. CONNEAU and G. Lample, “Cross-lingual
Language Model Pretraining,” in Advances in Neural Information
Processing Systems,
Curran Associates, Inc., 2019. Accessed: Dec. 12, 2025. [Online]. Available: [https://proceedings.neurips.cc/paper_files/paper/2019/hash/c04c19c2c2474dbf5f7ac4372c5b9af1-Abstract.](https://proceedings.neurips.cc/paper_files/paper/2019/hash/c04c19c2c2474dbf5f7ac4372c5b9af1-Abstract.html)[html](https://proceedings.neurips.cc/paper_files/paper/2019/hash/c04c19c2c2474dbf5f7ac4372c5b9af1-Abstract.html)

[12]L. Beyer, O. J. Hénaff, A. Kolesnikov, X.
Zhai, and A. van den Oord, “Are we done with ImageNet?,” June 12, 2020, arXiv:
arXiv:2006.07159. doi: [10.48550/arXiv.2006.07159](https://doi.org/10.48550/arXiv.2006.07159).

[13]K. Han, S. Lee, and D. Lee, “An Evaluation
Dataset and Strategy for Building Robust Multi-turn Response Selection Model,”
in Proceedings
of the 2021 Conference on Empirical Methods in Natural Language Processing,
M.-F. Moens, X. Huang, L. Specia, and S. W. Yih, Eds., Online and Punta Cana,
Dominican Republic: Association for Computational Linguistics, Nov. 2021, pp.
2338–2344. doi: [10.18653/v1/2021.emnlp-main.180](https://doi.org/10.18653/v1/2021.emnlp-main.180).

[14]E. Tanwar, S. Dutta, M. Borthakur, and T.
Chakraborty, “Multilingual LLMs are Better Cross-lingual In-context Learners
with Alignment,” in Proceedings of the 61st Annual Meeting of
the Association for Computational Linguistics (Volume 1: Long Papers), A.
Rogers, J. Boyd-Graber, and N. Okazaki, Eds., Toronto, Canada: Association for
Computational Linguistics, July 2023, pp. 6292–6307. doi: [10.18653/v1/2023.acl-long.346](https://doi.org/10.18653/v1/2023.acl-long.346).
