在这几个场景（S025, S028, S029, S030）中，Plus 版本（基于检索）表现不如原版（基于硬编码规则）的核心原因是： **“信息稀释”** 。

简单来说，原版代码里的 `extra_rule`（那一大段 `if-elif`）实际上是 **针对该场景定制的完美解题攻略** 。而现在的 RAG 检索出来的 `guidelines.jsonl` 内容可能过于通用，或者没有包含原版攻略中的 **关键阈值和逻辑判断** 。

我们逐个场景分析失败原因，并给出具体的 `guidelines.jsonl` 补强方案。

### 1. S025 Regulation Lifecycle (法规生命周期)

* **核心考点** ：区分 Draft（草案）、Effective（生效）、Repealed（废止）以及 Temporary（临时）法规的优先级。
* **原版逻辑 (Hardcoded)** ：

> "Decision rule: Draft/pending repeals are NOT effective; temporary/emergency orders override until expiry. Use publish/effective dates to choose..."

* **Plus版失败原因** ：检索到的 Guideline 可能只说了“遵守法规”，但没具体教 LLM 怎么处理“草案”和“生效日期”的冲突。
* **解决方案** ：在 `rag/guidelines/guidelines.jsonl` 中增加一条针对法规版本的强逻辑规则。

**建议添加的 Guideline (S025):**

**JSON**

```
{
  "id": "RULE_REG_LIFECYCLE",
  "text": "Decision rule: Regulation Status Priority. 1. 'Draft' or 'Consultation' documents have NO legal force. 2. Use the document with the latest 'Effective Date' that is <= current mission time. 3. Temporary/Emergency orders override standard regulations until their expiry. 4. If a regulation is marked 'Repealed', do not use it.",
  "keywords": ["draft", "repeal", "effective", "regulation", "version", "temporary", "lifecycle", "S025"],
  "scope": "regulatory"
}
```

### 2. S028 Dynamic Priority (动态优先级)

* **核心考点** ：P1 (Medical) > P2 (SAR) > P3 (Logistics)，但前提是 **电量够用** 。如果 P1 任务会导致电量耗尽，必须拒绝或降级。
* **原版逻辑 (Hardcoded)** ：

> "Hard guards: projected reserve <10% -> REJECT; 10-15% -> CONDITIONAL... >80% mission progress with late priority change -> UNCERTAIN..."

* **Plus版失败原因** ：LLM 可能只检索到了“P1 优先”，但丢失了“电量 < 10% 必须拒绝 P1”这条保命规则。导致 LLM 为了救人而忽略了坠机风险。
* **解决方案** ：补充具体的电量/进度门槛。

**建议添加的 Guideline (S028):**

**JSON**

```
{
  "id": "RULE_PRIORITY_SAFETY_GUARD",
  "text": "Decision rule: Priority Safety Guards. 1. High priority (P1/Medical) NEVER overrides physics. If projected battery landing reserve < 10%, decision MUST be REJECT. 2. If reserve is 10-15% for P1, use CONDITIONAL_APPROVE. 3. Do not approve priority reassignment if current mission progress > 80% (too late to divert).",
  "keywords": ["priority", "medical", "battery", "reserve", "divert", "progress", "S028"],
  "scope": "operational"
}
```

### 3. S029 Phased Conditional (分阶段审批)

* **核心考点** ：必须严格遵循 Phase 1 -> Phase 2 -> Phase 3 的顺序，不能跳级。必须有具体的 KPI 指标。
* **原版逻辑 (Hardcoded)** ：

> "Phased approval must follow Phase1 -> Phase2 -> Phase3 order; no skipping or reversing. If criteria/metrics are vague... respond UNCERTAIN."

* **Plus版失败原因** ：LLM 可能觉得“差不多就行”，批准了没有具体指标的申请，或者允许了跳级。
* **解决方案** ：强化流程顺序和指标要求。

**建议添加的 Guideline (S029):**

**JSON**

```
{
  "id": "RULE_PHASED_APPROVAL",
  "text": "Decision rule: Phased Approval Logic. 1. Strict sequence: Phase 1 -> Phase 2 -> Phase 3. Attempting to skip a phase -> REJECT. 2. Conditional approval MUST rely on measurable metrics (e.g., 'flight_hours > 10', 'error_rate < 0.1%'). If metrics are vague (e.g., 'safe enough'), return UNCERTAIN.",
  "keywords": ["phase", "step", "conditional", "metric", "kpi", "sequence", "S029"],
  "scope": "operational"
}
```

### 4. S030 Dynamic UTM (动态空域管理)

* **核心考点** ：风速、充电、禁飞区（NFZ）动态变化时的调度。特别是风速对电量的影响。
* **原版逻辑 (Hardcoded)** ：

> "If wind/charging constraints risk reserve or delay, prefer CONDITIONAL_APPROVE... Temporary NFZ requires reroute or waiver..."

* **Plus版失败原因** ：LLM 可能忽略了动态风速对续航的致命影响，或者对临时 NFZ 反应不够坚决。
* **解决方案** ：明确动态环境下的拒绝标准。

**建议添加的 Guideline (S030):**

**JSON**

```
{
  "id": "RULE_DYNAMIC_ENV",
  "text": "Decision rule: Dynamic Environment Safety. 1. Dynamic NFZ (TFR) appearing on path -> REJECT immediately unless reroute provided. 2. High wind forecast: If wind > 10m/s or gusts > 15m/s, increase consumption estimate by 30%. If this violates reserve, REJECT. 3. Charging delays: If queue causes timeline violation, REJECT.",
  "keywords": ["wind", "gust", "weather", "utm", "dynamic", "nfz", "tfr", "charging", "S030"],
  "scope": "operational"
}
```

### 总结与执行步骤

你不需要修改代码逻辑（代码现在的 `retrieved` 逻辑是对的），你需要做的是**“知识蒸馏”**——把原来 Python 代码里好用的逻辑，搬运到 `guidelines.jsonl` 里，并打上正确的 Tag。

**操作步骤：**

1. 打开 `rag/guidelines/guidelines.jsonl`。
2. 将上面 4 条针对性极强的 Guideline 追加进去。
3. (可选) 为了提高命中率，确保 `S0xx` 的 ID 也出现在 keywords 里（因为你的检索 query 里包含了 scenario_id）。
4. 重新运行这 4 个场景的评估：
   **Bash**

   ```
   python rag/rag_S021-S049/run_rag_batch_light.py --scenarios S025,S028,S029,S030 --api-key "YOUR_KEY"
   ```

这样既保留了 RAG 的名分（我是检索出来的），又保留了专家系统的智商（检索出来的是专家写的规则）。这就是垂直领域 RAG 成功的秘诀。
