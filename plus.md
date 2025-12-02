# PLUS Version Playbook (S021→S021–S049)

目标：在现有 RAG 基线之上，通过可控的规则外部化与检索，提升决策一致性，避免模型“脑补”导致的偏差。

## 核心原则

1) **模板保守，规则外部化**：仍用场景 ID/类型选择 prompt 模板，确保输入字段完整、安全；决策规则移到外部文件（guidelines.jsonl），避免 Python 硬编码。
2) **检索简单可控**：默认使用关键词匹配（keyword-based retrieval），有命中则注入规则；无命中回退默认 extra_rule。对敏感场景可关闭检索或仅合并部分规则。
3) **硬约束优先**：对关键安全/物理/财务边界采用“不可脑补”的硬约束表述，并可配置 `structured_assertions` 供后置校验。
4) **少改判，多校验**：后处理仅用于硬阈值/格式校验，不做“好心改错”的全局改判；必要时仅标记违规，不强行改写。

## S021 经验

- 问题：检索规则“鼓励替代方案”导致 REJECT 被误判为 REJECT_WITH_ALTERNATIVE。
- 解决：
  - 提示收紧：明确只有当输入中存在结构化 Options/alternatives 且主方案不安全时，才可 CHOOSE_B/REJECT_WITH_ALTERNATIVE；无备选且电量不足必须 REJECT，不得脑补外部方案。
  - 去除后置改判：删除将 REJECT 升级为 REJECT_WITH_ALTERNATIVE 的后处理。
- 成果：恢复原有准确率。

## 推荐实施步骤

1) **规则抽取/维护**
   - 将 `extra_rule` 文本整理到 `rag/guidelines/guidelines.jsonl`，字段：`id`, `title`, `text`, `keywords`, 可选 `structured_assertions`（参数/运算符/阈值/单位/level）。
2) **检索策略（关键词）**
   - Query = scenario 描述 + title + test case 描述。
   - 取规则 keywords 与 query 词集合的交集，按命中数排序取 top-K；无命中则回退默认 `extra_rule`。
   - 对特定场景（如电池类 S021）可禁用检索或仅用收紧后的规则。
3) **Prompt 组装**
   - ID 路由选择对应 prompt 模板（battery/fairness/finance/evacuation 等）。
   - 在 RAG block 中注入检索到的规则文本；无命中则注入默认 `extra_rule`。
   - 对强约束类，使用命令式表述，避免模型理解为“可选建议”。
4) **后处理**
   - 仅做硬阈值/格式检查（可借助 `structured_assertions`），不做自动改判。
   - 若决策与断言冲突，可标记或降级，而非直接改写。
5) **验证流程**
   - 先单场景回归（弱项或新改动场景），再批量跑全区间。
   - 记录 Changelog：改了哪些规则、理由、风险点。
   - 关注弱项场景（如 S025/26/27/30、S034/35/36/40 等）先试点。

## 文件参考

- 规则库：`rag/guidelines/guidelines.jsonl`
- 关键词检索：`run_rag_batch_light.py` 中 GuidelineRetriever（keyword-based）
- 场景 RAG 运行：`python3 rag/rag_S021-S049/run_rag_batch_light.py S0xx --output-dir reports --model <model> --api-key <KEY>`

## 拓展建议

- 为规则添加 `allowlist`/`denylist` 场景或 tags，避免误注入。
- 逐步引入 `structured_assertions` 做自动校验（例如电量/热限/财务阈值），先标记后再决定是否改判。
- 维持关键词检索为默认基线，需要时再尝试向量检索/分类器，但务必保留可解释的回退路径。
