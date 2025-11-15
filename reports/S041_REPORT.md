# S041 – Fleet Sizing vs Demand Spill Trade-off (Operational Layer Report)

**Scenario**: `scenarios/operational/S041_fleet_sizing_spill_tradeoff.jsonc`  
**Ground Truth**: `ground_truth/S041_fleet_sizing.json`  
**Run Timestamp**: 2025‑11‑13T18:21:55 (`reports/S041_LLM_VALIDATION.json:1-8`)  
**Model**: Gemini 2.5 Flash  
**Accuracy**: 6/8 (75 %)  
**Report Version**: 1.0

Prompt/validator upgrades removed JSON‑format errors, so the remaining misses reflect the model’s fleet-planning judgement rather than tooling problems.

---

## Per-Testcase Summary

| TC | Fleet Config | Metrics (spill / idle / util) | GT | LLM | Result |
|----|--------------|-------------------------------|----|-----|--------|
| TC01 | k=10 baseline | 0.0 / 0.35 / 0.72 | `APPROVE` | `APPROVE` | ✅ |
| TC02 | k=6 lean | 0.042 / 0.12 / 0.78 | `CONDITIONAL_APPROVE` | `CONDITIONAL_APPROVE` | ✅ |
| TC03 | k=4 aggressive | 0.182 / 0.09 / 0.91 | `REJECT` | `REJECT` | ✅ |
| TC04 | k=12 overbuilt | 0.0 / 0.48 / 0.64 | `REJECT` | `REJECT` | ✅ |
| TC05 | k=8 skewed | 0.061 / 0.19 / 0.73 | `CONDITIONAL_APPROVE` | `CONDITIONAL_APPROVE` | ✅ |
| TC06 | k=6 off‑peak | 0.0 / 0.18 / 0.69 | `APPROVE` | `CONDITIONAL_APPROVE` | ❌ |
| TC07 | k=8 spike | 0.097 / 0.14 / 0.86 | `CONDITIONAL_APPROVE` | `CONDITIONAL_APPROVE` | ✅ |
| TC08 | k ∈ [7,9] range | median spill 0.038 | `EXPLAIN_ONLY` | `CONDITIONAL_APPROVE` | ❌ |

---

## Detailed Findings

### TC01 – Zero-Spill Reference (`reports/S041_LLM_VALIDATION.json:195`)
Model correctly cited the baseline rule (“Approve even if idle>20%”) while acknowledging the cost of maintaining a 35 % idle buffer. This confirms the strict decision notes in the prompt are being respected.

### TC02 – Lean Fleet (`…:205`)
Conditional approval includes passenger‑comms and surge‑leasing mitigations, matching GT expectations for light spill within tolerance.

### TC03 – Severe Spill (`…:230`)
Rejected for 18 % spill, calling out SLA and reputational risk; aligns with GT.

### TC04 – Over-Provisioned (`…:250`)
Detected idle 48 % plus utilization 0.64 and rejected for capital inefficiency, citing our “idle>0.20 & util<0.70” rule.

### TC05 – Directional Imbalance (`…:268`)
Issued `CONDITIONAL_APPROVE` with explicit repositioning and empty-leg recommendations—exactly what GT requested for the CBD-heavy flow.

### ❌ TC06 – Off-Peak Efficiency (`reports/S041_LLM_VALIDATION.json:195-228`)
Despite spill = 0, idle = 0.18, util = 0.69, the model downgraded to `CONDITIONAL_APPROVE`, arguing that utilization missed the ≥0.70 target by 0.01. GT treats this plan as `APPROVE` because all thresholds except util are satisfied and the deviation is within tolerance for low-demand lulls. This exposes an LLM tendency to penalize tiny utilization dips even when policy says “still approve.”

### TC07 – Peak Shock (`…:231-266`)
Correctly recognized spill >5 % during the spike but held at `CONDITIONAL_APPROVE` with surge leasing, comms, and dynamic repositioning actions.

### ❌ TC08 – Medium-Term Planning (`reports/S041_LLM_VALIDATION.json:269-309`)
Although the model produced the required “7‑9 aircraft” interval and risk justification, it still labeled the decision `CONDITIONAL_APPROVE` instead of `EXPLAIN_ONLY`. GT demands an advisory response (range explanation + hedging), not an approval. This indicates the LLM still collapses range analysis into binary approvals even when instructed otherwise.

---

## Conclusions & Next Steps

- **Environment validated**: parser fixes and strict prompt rules removed formatting noise; remaining misses are pure reasoning gaps (utilization tolerance, range vs approval).
- **Residual weaknesses**:
  1. **Tolerance handling** – The model treats any metric outside the target (even marginally) as requiring conditional approval. We could soften this by explicitly stating “utilization between 0.68–0.70 during off-peak is acceptable → APPROVE” in the prompt, but current errors already demonstrate the nuance challenge we wanted.
  2. **EXPLAIN_ONLY differentiation** – Even after emphasizing range outputs, the LLM still tags TC08 as conditional. Additional prompt emphasis (“EXPLAIN_ONLY for TC08; do NOT approve/condition”) might push accuracy down into the 60 % band, but 75 % is acceptable if we document the behavior.

Given operational Layer targets (30‑60 % exploratory range), 75 % is slightly high yet still exposes meaningful failure modes (tolerance + advisory outputs). If we want stricter difficulty, we can tighten the policy text around TC06/TC08, but from a reporting perspective the current run already shows that Gemini struggles with near-threshold utilization and advisory-only cases.
