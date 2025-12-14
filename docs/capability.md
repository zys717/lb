# Low-Altitude Economy AI Capabilities: Literature Review & Scenario Mapping

## 1. 概述 (Executive Summary)

本报告旨在为低空经济（Low-Altitude Economy, LAE）智能体构建一套基于学术文献的能力评估框架。报告首先通过调研顶刊文献总结了  **7 大核心能力簇（Y轴）** ，然后严格依据本项目（LAE-Bench）定义的  **4 个成熟度层级（X轴）** ，将 49 个场景（S001-S049）及其测试用例（TC）进行了精准映射。

此矩阵旨在揭示当前测试集的覆盖热点与能力边界，为后续绘制评估热力图提供数据支撑。

## 2. 维度定义 (Axis Definitions)

### 2.1 X轴：场景成熟度层级 (Project Layers)

依据项目目录结构 (`scenarios/basic`, `intermediate`, `advanced`, `operational`) 划分：

* **Layer 1: Basic (基础合规层)**
  * **范围** : S001 – S020
  * **定义** : 确定性的物理与法规检查。包括地理围栏、时空限制、飞行包线、基础空域规则。
  * **对应文献** : FAA Part 107, U-space U1/U2 services.
* **Layer 2: Intermediate (动态决策层)**
  * **范围** : S021 – S030
  * **定义** : 引入动态变量与价值权衡。包括突发状况处理、规则冲突解决、优先级排序、机器伦理。
  * **对应文献** : ASTM F3411-22 (Remote ID), U-space U3 services.
* **Layer 3: Advanced (认知推理层)**
  * **范围** : S031 – S040
  * **定义** : 处理高阶认知挑战。包括意图识别、模糊指令消歧、因果推理、安全防御与对抗性测试。
  * **对应文献** : AI Safety in Aviation, SOTIF (Safety of the Intended Functionality).
* **Layer 4: Operational (运营运筹层)**
  * **范围** : S041 – S049
  * **定义** : 系统级的大规模优化。包括机队管理、能源策略、公平性分配、基础设施联动。
  * **对应文献** : Urban Air Mobility (UAM) Fleet Management, Vertiport Operations.

### 2.2 Y轴：核心能力簇 (Capability Clusters)

基于文献调研归纳的 7 项核心能力：

1. **Spatial & Physical Awareness (空间与物理感知)** : 对三维空间、障碍物、飞行器运动学限制的理解。
2. **Regulatory Compliance (法规合规校验)** : 对静态法规（如禁飞区、限高、时段）的刚性执行。
3. **Dynamic Contingency (动态应急响应)** : 处理飞行中突发的电量、链路、天气或设备故障。
4. **Cognitive & Ethical Reasoning (认知与伦理推理)** : 处理模糊规则、电车难题、因果关系及隐性常识。
5. **Interaction & Security (交互与安全防御)** : 理解人类自然语言意图、防御欺骗攻击、鉴权。
6. **Resource & Fleet Optimization (资源与机队运筹)** : 能源管理、运力分配、多机协同。
7. **Systemic Fairness & Coordination (系统公平与协同)** : 多运营商博弈、空域谈判、社会公平性。

## 3. 热力矩阵数据源 (Heatmap Data Source)

**请使用下表数据绘制热力图：**

| **Capability Cluster (Y-Axis)**      | **Layer 1: Basic (S001-S020)**                              | **Layer 2: Inter. (S021-S030)**     | **Layer 3: Adv. (S031-S040)**       | **Layer 4: Ops (S041-S049)** |
| ------------------------------------------ | ----------------------------------------------------------------- | ----------------------------------------- | ----------------------------------------- | ---------------------------------- |
| **1. Spatial & Physical Awareness**  | **9**(S001, S002, S003, S006, S007, S009, S010, S015, S016) | 0                                         | **1**(S036)                         | 0                                  |
| **2. Regulatory Compliance**         | **9**(S004, S005, S008, S011, S012, S013, S014, S017, S019) | **3**(S023, S025, S030)             | 0                                         | 0                                  |
| **3. Dynamic Contingency**           | 0                                                                 | **2**(S021, S024)                   | **1**(S031)                         | **2**(S044, S048)            |
| **4. Cognitive & Ethical Reasoning** | 0                                                                 | **5**(S022, S026, S027, S028, S029) | **3**(S037, S038, S039)             | 0                                  |
| **5. Interaction & Security**        | **1**(S020)                                                 | 0                                         | **5**(S032, S033, S034, S035, S040) | **1**(S045)                  |
| **6. Resource & Fleet Optimization** | **1**(S018)                                                 | 0                                         | 0                                         | **3**(S041, S042, S043)      |
| **7. Systemic Fairness & Coord.**    | 0                                                                 | 0                                         | 0                                         | **3**(S046, S047, S049)      |

*(注：S018在Basic层是基础多机协同；S020虽是Basic但涉及审批交互流程归为Interaction；具体分类依据见下文详细分析)*

## 4. 详细映射分析与文献支撑 (Detailed Analysis)

### 4.1 Layer 1: Basic (S001-S020) — 数字化基石

 **核心特征** : 刚性规则 (Hard Constraints)、单机视角、确定性输入。

* **Spatial & Physical (9 scenarios)** :
* **S001, S002 (Geofence)** : 对应 **Eurocae ED-269** 标准，测试多边形围栏内/外判定。
* **S003 (Path)** : 对应  **ASTM F3548-21** ，测试4D轨迹相交检测。
* **S006, S007, S009, S010 (Alt/Speed)** : 对应 **FAA Part 107.51** 运行限制。
* **S015, S016 (Obstacle/NFZ)** : 对应 **RTCA DO-365** (Detect and Avoid)，测试对动态障碍的反应。
* **Regulatory Compliance (9 scenarios)** :
* **S004 (Airport)** ,  **S005 (TFR)** : 对应 **FAA LAANC** 系统的数据接入能力。
* **S008 (Waiver)** : 测试 Part 107.51(b) 关于高层建筑周边限高豁免的逻辑。
* **S011 (Night), S012 (Time), S013 (VLOS), S014 (BVLOS)** : 基础运行规章检查。
* **S017 (Payload)** ,  **S019 (Airspace)** : 空域分类与危险品运输规则。
* **Others** :
* **S018 (Multi-Drone)** : 基础编队防撞（属于 Resource 雏形）。
* **S020 (Timeline)** : 行政审批时效（属于 Interaction 雏形）。

> **文献支撑** : [Prats et al., 2020] 指出 U1/U2 阶段的核心是 e-identification 和 geofencing。本层级完美覆盖了这一基础需求。

### 4.2 Layer 2: Intermediate (S021-S030) — 动态与伦理

 **核心特征** : 价值冲突 (Conflict of Values)、动态环境、软约束。

* **Cognitive & Ethical (5 scenarios)** :
* **S022 (Rule Conflict)** : 当法规（如限高）与安全（如避障）冲突时的公理排序。
* **S026 (Ethical Trilemma)** : 机器伦理经典问题（损财 vs 伤人风险）。对应 **[IEEE T-ITS, 2023]** 关于自动驾驶伦理的研究。
* **S027 (Biz vs Safety)** : 商业压力下的安全底线测试（Safety Culture）。
* **S028 (Dynamic Priority)** : 医疗 vs 商业的优先级动态调整。
* **S029 (Phased)** : 时序逻辑推理（Before/After/Unless）。
* **Dynamic Contingency (2 scenarios)** :
* **S021 (Battery Emergency)** : 经典的 "Land Now" vs "Return to Home" 决策边界测试。
* **S024 (Conflict Sources)** : 处理多源数据冲突（传感器 vs 气象台）。
* **Regulatory Compliance (3 scenarios)** :
* **S023 (Reg Update)** : 知识库截止日期与法规更新的测试。
* **S025 (Lifecycle)** ,  **S030 (UTM)** : 全生命周期管理与 UTM 指令依从。

> **文献支撑** : [Cohen et al., 2021] 强调 UAM 运营中必须解决 "Social Acceptance" 和 "Equity" 问题，S026/S028 直接响应了这一需求。

### 4.3 Layer 3: Advanced (S031-S040) — 认知与对抗

 **核心特征** : 不确定性 (Uncertainty)、人类交互 (HMI)、安全性 (Security)。

* **Interaction & Security (5 scenarios)** :
* **S032 (Ambiguity)** : 处理 "Land near the park" 这种模糊指令，测试 **NLU (Natural Language Understanding)** 的消歧能力。
* **S034 (Intent)** : 识别用户的深层意图（如为了新闻拍摄而申请飞越火灾现场）。
* **S035 (Authority)** : 防御伪造的 UTM 指令（Security/Spoofing）。
* **S033 (Dyn Priority II)** : 多智能体间的复杂协商博弈。
* **S040 (Loopholes)** : 红队测试（Red Teaming），识别利用规则漏洞的行为。
* **Cognitive Reasoning (3 scenarios)** :
* **S037 (Implicit)** : 推理隐性规则（未明文规定但约定俗成的右行/避让规则）。
* **S038 (Causal)** : 故障归因与因果链推理。
* **S039 (Epistemic)** : 在信息缺失（Unknown Unknowns）情况下的保守决策。
* **Others** :
* **S031 (Medical Nested)** : 复杂的嵌套条件逻辑。
* **S036 (Boundary)** : 针对地理围栏边缘的对抗性探测（Spatial 进阶版）。

> **文献支撑** : [MDPI Aerospace, 2025] 提出利用 LLM 进行航空事故归因（HFACS-LLM），S038 和 S039 测试了模型是否具备类似的因果推理与不确定性管理能力。

### 4.4 Layer 4: Operational (S041-S049) — 规模化运筹

 **核心特征** : 群体智能 (Swarm)、经济性 (Economics)、系统最优。

* **Resource & Fleet Optimization (3 scenarios)** :
* **S041 (Fleet Sizing)** : 需求预测与机队规模匹配（运筹学问题）。
* **S042 (Charging)** : 电池寿命 vs 运营效率的优化策略。
* **S043 (Repositioning)** : 解决供需不平衡的动态调度（Rebalancing）。
* **Systemic Fairness & Coordination (3 scenarios)** :
* **S046 (Vertiport)** : 基础设施容量限制下的排队论问题。
* **S047 (Fairness)** : 多运营商之间的空域资源公平分配（基尼系数）。
* **S049 (Emergency Cap)** : 极限压力下的系统降级与熔断机制。
* **Dynamic Contingency (2 scenarios)** :
* **S044 (Batt Ops)** : 机队级连锁故障处理。
* **S048 (Evacuation)** : 灾难场景下吞吐量最大化的撤离路径规划。
* **Interaction (1 scenario)** :
* **S045 (Airspace Conflict)** : 运营商之间的战略级谈判与妥协。

> **文献支撑** : [Kellermann et al., 2020] 在 "Barriers to UAM" 中指出，电网负载（S042）、空域公平性（S047）和垂直起降场吞吐量（S046）是商业化落地的三大瓶颈。

## 5. 关键参考文献 (Selected References)

[1]D. Falanga, K. Kleber, and D. Scaramuzza,
“Dynamic obstacle avoidance for quadrotors with event cameras,” Science
Robotics,
vol. 5, no. 40, p. eaaz9712, Mar. 2020, doi: [10.1126/scirobotics.aaz9712](https://doi.org/10.1126/scirobotics.aaz9712).

[2]Z. Jian et al.,
“Dynamic Control Barrier Function-based Model Predictive Control to
Safety-Critical Obstacle-Avoidance of Mobile Robot,” in 2023
IEEE International Conference on Robotics and Automation (ICRA), May
2023, pp. 3679–3685. doi: [10.1109/ICRA48891.2023.10160857](https://doi.org/10.1109/ICRA48891.2023.10160857).

[3]W. Sun, G. Tang, and K. Hauser, “Fast UAV
Trajectory Optimization using Bilevel Optimization with Analytical Gradients,”
in 2020
American Control Conference (ACC), July 2020, pp. 82–87. doi: [10.23919/ACC45564.2020.9147300](https://doi.org/10.23919/ACC45564.2020.9147300).

[4]Unmanned Aircraft
System (UAS) Traffic Management (UTM)

[5] Drone Integration: Concept of
Operations (May 2025)

[6]A. Li, M. Hansen, and B. Zou, “Traffic
management and resource allocation for UAV-based parcel delivery in
low-altitude urban space,” Transportation Research Part C: Emerging
Technologies,
vol. 143, p. 103808, Oct. 2022, doi: [10.1016/j.trc.2022.103808](https://doi.org/10.1016/j.trc.2022.103808).

[7]Y. Liu, “Large language models for air
transportation: A critical review,” Journal of the Air Transport
Research Society,
vol. 2, p. 100024, June 2024, doi: [10.1016/j.jatrs.2024.100024](https://doi.org/10.1016/j.jatrs.2024.100024).

[8]Y. Wang, J. Ji, Q. Wang, C. Xu, and F.
Gao, “Autonomous Flights in Dynamic Environments with Onboard Vision,” in 2021
IEEE/RSJ International Conference on Intelligent Robots and Systems (IROS),
Sept. 2021, pp. 1966–1973. doi: [10.1109/IROS51168.2021.9636117](https://doi.org/10.1109/IROS51168.2021.9636117).

[9]J. Andriuškevičius and J. Sun, “Automatic
Control With Human-Like Reasoning: Exploring Language Model Embodied Air
Traffic Agents,” Sept. 15, 2024, arXiv: arXiv:2409.09717. doi: [10.48550/arXiv.2409.09717](https://doi.org/10.48550/arXiv.2409.09717).

[10]Z. Li, B. Peng, P. He, and X. Yan,
“Evaluating the Instruction-Following Robustness of Large Language Models to
Prompt Injection,” in Proceedings of the 2024 Conference on
Empirical Methods in Natural Language Processing, Y. Al-Onaizan, M. Bansal, and Y.-N.
Chen, Eds., Miami, Florida, USA: Association for Computational Linguistics,
Nov. 2024, pp. 557–568. doi: [10.18653/v1/2024.emnlp-main.33](https://doi.org/10.18653/v1/2024.emnlp-main.33).

[11]V. Raina, A. Liusie, and M. Gales, “Is
LLM-as-a-Judge Robust? Investigating Universal Adversarial Attacks on Zero-shot
LLM Assessment,” in Proceedings of the 2024 Conference on
Empirical Methods in Natural Language Processing, Miami, Florida, USA: Association for
Computational Linguistics, 2024, pp. 7499–7517. doi: [10.18653/v1/2024.emnlp-main.427](https://doi.org/10.18653/v1/2024.emnlp-main.427).

[12]B. Balázs, T. Vicsek, G. Somorjai, T.
Nepusz, and G. Vásárhelyi, “Decentralized traffic management of autonomous
drones,” Swarm
Intell,
vol. 19, no. 1, pp. 29–53, Mar. 2025, doi: [10.1007/s11721-024-00241-y](https://doi.org/10.1007/s11721-024-00241-y).

[13]Y. Tian et al.,
“UAVs Meet LLMs: Overviews and Perspectives Toward Agentic Low-Altitude
Mobility,” Information
Fusion,
vol. 122, p. 103158, Oct. 2025, doi: [10.1016/j.inffus.2025.103158](https://doi.org/10.1016/j.inffus.2025.103158).

[14]A. Hamissi and A. Dhraief, “A Survey on
the Unmanned Aircraft System Traffic Management,” ACM
Comput. Surv.,
vol. 56, no. 3, pp. 1–37, Mar. 2024, doi: [10.1145/3617992](https://doi.org/10.1145/3617992).

[15]S. Javaid, H. Fahim, B. He, and N. Saeed,
“Large Language Models for UAVs: Current State and Pathways to the Future,” IEEE
Open Journal of Vehicular Technology, vol. 5, pp. 1166–1192, 2024, doi: [10.1109/OJVT.2024.3446799](https://doi.org/10.1109/OJVT.2024.3446799).
