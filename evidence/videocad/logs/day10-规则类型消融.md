# Day10 规则类型消融实验日志（plan v1 步骤三）

日期：2026-09-16

## 任务

拆开"最小规则集"，报四类规则（合法集 / 顺序 / 一致性 / 坐标）的边际贡献、覆盖率与收缩比（方案 v1 步骤三，表 D/E）。9 消融条件 + no_rules 参照臂 = 10 条件，全部无重试（ρ/k 不适用）。产出供论文图 4 使用。主实验（四臂确认集，种子 20261015）已完成且门 v2 通过，本步为其后续。

## 参数

| 项 | 设定 |
|---|---|
| 脚本 | `scripts/run_rule_ablation.py`（新文件；从 `run_four_arm_experiment.py` **导入**原语，非复制——两源模块均有 main-guard，import 无副作用，与 `bootstrap_eps_star.py` 同一导入先例） |
| 样本 | `confirm_set_600.csv` 全 600 链（200/200/200，`--use-all-rows` 语义） |
| replicates | 20 |
| ε 网格 | 主口径 PRIMARY = {0.02, 0.05, 0.08}（plan v1 表 E 预登记 3 点）+ 扩展区 EXTENDED = {0.10, 0.14, 0.18, 0.22, 0.26, 0.30, 0.34}（exploratory），并集 10 点一次跑全，输出逐行标注 primary/exploratory |
| budget-ratio | 0.2（B = ceil(L×1.2)；无重试下恒不约束，保留同口径） |
| swap-prob | 0.7 |
| 种子 | **20261016**（与主跑批 20261015 错开一日：主确认集种子已预登记"只运行一次"，不得复用；本消融为新实验，取相邻次日保持血缘可读并避免任何"重跑确认集"的解释空间；F2 配对设计下换种子仅等价于独立重复抽样） |
| 判据 | ε* 主判据 0.5，引擎同一插值函数（导入） |
| 运行量 | 10 条件 × 600 链 × 10 ε × 20 rep = **1,200,000 runs**，实测 **60.7 s**（≈19.8k runs/s） |

## ε 网格理由（必须写明的口径史）

消融 3 点网格（0.02/0.05/0.08）源自 plan v1 时代——当时依据的是被 F1 撤回的伪造 JSON 世界观（ε*≤0.08），**是假 JSON 世界观第三次咬伤的受害者**。处置：主口径 3 点保留（保预登记一致性，其上 Δε* 预计全删失，如实报 censored 不省略）；扩展区按 audit §3.1 先例（网格上限必须盖住真实 ε*：开发集 min_rules 分层 ε* 最高 0.3259 → 顶端取 0.34 防删失），**用户 2026-09-16 批准**。

## 四类规则的操作化定义与引擎原语映射（申报）

引擎 `min_rules_repair` 三处修复原语归属：

| 类 | 原语 | 说明 |
|---|---|---|
| 合法集 | R3 非法关闭修正（空栈 finished → started）+ R1 状态字母表修复（读 gt，oracle 通道申报；本误差模型下**死代码**，实测全程触发 0 次） | 状态条件合法集：空栈态合法集 = {started}；即 proposal 的"限制非法状态扩散" |
| 一致性 | R2 栈一致性收束（finish 投影到栈顶） | finish 的状态前后条件；proposal 出处：1.3-科学问题 §1.3.4、研究内容 WP1-WP2-WP3:76、申报书正文总稿-V1.md:111 |
| 顺序 | **无独立原语** | LIFO 关闭次序纪律内嵌于 R2 的栈顶投影，不可分离为独立可开关代码路径 → only_order ≡ no_rules、loo_no_order ≡ full（构造性退化，F5 软版本同性质，如实报告为范围发现） |
| 坐标 | **无对应物** | 坐标是图像侧概念，符号动作链上不存在 → only_coordinate ≡ no_rules、loo_no_coordinate ≡ full（vacuous，如实报告） |

全集条件逐语义等于引擎 min_rules（同一修复代码路径：导入原语组合施加；另对全部可达状态空间 status×action×gt×栈内容做了穷举等价验证）。

## 产物

- `evidence/videocad/notes/rule_ablation/per_run_results.csv`（1,200,000 runs，逐 run 含各类触发步数）
- `evidence/videocad/notes/rule_ablation/curve_summary.csv`（300 行：条件 × 层 × ε）
- `evidence/videocad/notes/rule_ablation/eps_star.csv`（80 行：条件 × 层/pooled × 两档网格）
- `evidence/videocad/notes/rule_ablation/ablation_effects.csv`（1,152 行：Δ成功率 / Δε* / Δ失败位置，两方向长表）
- `evidence/videocad/notes/rule_ablation/coverage_contraction.csv`（440 行：覆盖率 + 收缩比，含 ALL 汇总行）
- `evidence/videocad/notes/rule_ablation/summary.json`（全参数 + 种子理由 + 网格理由 + 条件定义 + 规则映射 + metric_definitions + 运行计数 + 验证结果）

## 验证结论（a–e 全过）

- **a) 全集 ≡ 引擎 min_rules**：150 个随机 (chain, ε, rep) 三元组逐字段（success/fail_reason/attempts/mismatch/repaired）比对，**0 处不等**；另有状态空间穷举等价验证。
- **b) no_rules ≡ 引擎 no_rules**：同法 150 三元组，**0 处不等**。
- **c) 单调性**：每个 ε × 层/pooled（40 格）full 成功率 ≥ 任一留一成功率，**0 处违反**（机制上按构造成立：修复类只在无修复路径环境报错处触发，逐 run 支配）。
- **d) vacuous 条件**：order、coordinate 两类在所有启用条件中触发数恒为 0，显式标注 vacuous；构造性退化实证：only_order ≡ no_rules、only_coordinate ≡ no_rules、loo_no_order ≡ full、loo_no_coordinate ≡ full（全部成功计数逐格相等）。
- **e) 运行计数**：1,200,000 / 1,200,000 一致；实测 60.7 s（分钟级，符合预估）。
- 附：R1 死代码触发数 = 0（预期一致）；R3 触发 268,834 步。
- KS 检验（失败位置 vs no_rules）：**skipped**，理由已写入 summary.json（mean/median 足以支撑图 4 与正文表述；KS 为分布级补充，不进入任何预登记判定）。

## Headline 结果

### Δ成功率（pooled，主口径 3 点）

| 条件 | 方向 | ε=0.02 | ε=0.05 | ε=0.08 |
|---|---|---|---|---|
| only_legal_set | single − no_rules | +0.0158 | +0.0114 | +0.0082 |
| only_order | single − no_rules | 0（vacuous） | 0 | 0 |
| only_consistency | single − no_rules | **+0.3437** | **+0.3984** | **+0.3512** |
| only_coordinate | single − no_rules | 0（vacuous） | 0 | 0 |
| loo_no_legal_set | LOO − full | −0.1075 | −0.2071 | −0.2567 |
| loo_no_order | LOO − full | 0（vacuous） | 0 | 0 |
| loo_no_consistency | LOO − full | **−0.4353** | **−0.5941** | **−0.5998** |
| loo_no_coordinate | LOO − full | 0（vacuous） | 0 | 0 |
| full（补充口径） | − no_rules | +0.4512 | +0.6055 | +0.6079 |

读法：**一致性收束是主力**（单独启用即拿走全集增益的约六成）；合法集单独贡献微小，但必要性在全集组态中显现（拿掉它 −0.11~−0.26）——因为一致收束让链存活更久，合法集修复才有触发机会（覆盖率的条件间差异如实反映这一交互：legal_set 触发率在 only 条件 0.138% vs 全集 1.484%）。

### Δε*（pooled，插值，删失如实标）

| 条件 | primary 3 点 | extended 10 点 |
|---|---|---|
| no_rules | 0.02（left_censored） | 0.02（left_censored） |
| only_legal_set | 0.02（left_censored） | 0.02（left_censored） |
| only_consistency | 0.0599 | 0.0599 |
| only_order / only_coordinate | 0.02（left_censored；≡ no_rules） | 同左 |
| loo_no_legal_set | 删失（undefined） | 0.0599 |
| loo_no_consistency | 删失（undefined） | 0.02（left_censored） |
| loo_no_order / loo_no_coordinate | 删失（≡ full） | 0.1929（≡ full） |
| full | **right_censored（删失，如实报）** | **0.1929** |

主口径 3 点上 LOO 方向 Δε* 全部删失（undefined，right_censored），与预判一致；扩展区（exploratory）上全集 Δε* = +0.173（vs no_rules）。分层（extended）：full low 0.2946 / medium 0.1998 / high 0.1172（开发集 min_rules 对照 0.3259/0.2143/0.1112，量级一致）。

### 覆盖率 / 收缩比

| 类 | 触发步比例（全集条件） | 收缩比（触发步） |
|---|---|---|
| 一致性 | 14.88% | 0.8333（= 1 − 1/\|V\|，\|V\|=6：finish 候选动作集 → 栈顶 1 个） |
| 合法集 | 1.48% | 0.5（{started, finished} → {started}） |
| 顺序 | 0（vacuous） | — |
| 坐标 | 0（vacuous） | — |

收缩比操作化定义（引擎候选集是隐式的，本次申报的定义）：触发步上 1 − |约束后可行集| / |约束前可行集|，按规则所约束的维度计（详见 summary.json metric_definitions）。

## 与既有结果的一致性

全集条件 ε*（pooled，extended 10 点，种子 20261016）= **0.192883**；确认集 min_rules（26 点网格，种子 20261015）= **0.193418**。差 −0.00054 ≪ 0.01，符合"换种子仅抽样噪声"的预期（F2 配对设计的一致性证据）；同日批内 min_rules ε* 跨 ρ/r 逐位相同（0.193418，range=0），本次独立种子再现 0.1929，互为印证。

## 边界与范围声明

1. 本实验为符号动作链上的模拟研究（同主实验范围声明）；坐标类在符号链上无对应物是**范围事实**而非遗漏，与 proposal 的"坐标/落点一致性"属图像侧验证范围一致。
2. only_order / only_coordinate ≡ no_rules、loo_no_order / loo_no_coordinate ≡ full 是**构造性退化**（与 F5 rules_retry 退化的软版本同性质），图 4 应将其呈现为结构发现，不得解读为"顺序/坐标规则无效"的实证结果。
3. 扩展区 7 点为 exploratory（audit §3.1 先例 + 用户 2026-09-16 批准），不进入任何预登记判定族。
