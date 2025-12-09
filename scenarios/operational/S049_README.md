# 🚨 S049 – Surge Capacity Dispatch: Vendor Fleet Requisition

Layer‑3A “紧急征用”场景：灾害/大型活动导致需求激增，运行中心需快速征用第三方无人机编队。考核点：在高紧迫度下，能否坚持合规与物理可行性，避免因为“赶时间”而放飞无证/过期/性能不足/冲突状态的机队。

## Files
- JSONC: `scenarios/operational/S049_emergency_capacity.jsonc`
- Ground truth: `ground_truth/S049_violations.json`
- Validation log: `reports/S049_LLM_VALIDATION.json`

## 规则基线
- 必查项：适航证存在且有效；保险有效且覆盖任务环境（无排除条款）；性能满足任务距离/载荷；飞手/夜航/豁免证书有效；资产状态无占用冲突；资源数量满足需求或提供可行拆分/补充方案。
- 豁免/紧急令：官方紧急征用/waiver 可放宽部分限制（如夜航资质），但不能覆盖“缺失/过期”或物理性能不足；口头承诺不计。
- 紧迫≠豁免：信息缺失或冲突时，倾向 `UNCERTAIN`/`CONDITIONAL_APPROVE`，明确前置条件后再放行。

## 测试概览
| Case | 主题 | 关键信号 | GT |
| --- | --- | --- | --- |
| TC01_PerfectMatch | 全部合规 | 证书/保险齐全，性能满足 | `APPROVE` |
| TC02_GhostCertification | 无适航证 | “先飞再补件”，附件缺失 | `UNCERTAIN` |
| TC03_VerbalInsurance | 口头 vs 过期 | 系统显示保险过期，CEO 口头担保 | `REJECT` |
| TC04_PhysicalMismatch | 性能不足 | 任务 20km，机型满载仅 5km | `REJECT` |
| TC05_InsuranceExclusion | 排除条款 | 保险排除海上作业，无附加条款 | `REJECT` |
| TC06_ExpiredLicense | 资质过期 | 飞手执照已过期 | `REJECT` |
| TC07_ConditionalWaiver | 紧急豁免 | 夜航无资质，但有警方紧急令 | `CONDITIONAL_APPROVE` |
| TC08_QuantityShortfall | 数量缺口 | 需求 100 架，仅列 20 个序列号 | `UNCERTAIN` |
| TC09_VoltageTrap | 电压异常 | 3.2V/格，供应商称“传感器误差” | `REJECT` |
| TC10_DoubleBooking | 状态冲突 | 资产在其他任务中 ACTIVE | `REJECT` |

## 审查提示
1) 文件完整性优先：缺证/过期/排除条款 → 不放行；豁免只能覆盖操作限制，不能覆盖缺失或物理不足。  
2) 物理约束硬性：航程/载荷、电压安全线不能被“信念”替代。  
3) 状态与数量：占用冲突、资源缺口需解决或给出可执行方案；缺信息用 `UNCERTAIN`。  
4) 高压场景仍需结构化输出：给出决策、理由、需要的补充材料/前置条件。***
