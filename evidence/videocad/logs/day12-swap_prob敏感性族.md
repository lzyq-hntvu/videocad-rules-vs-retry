# Day 12 — swap_prob 敏感性族（audit §3.2⑦ 修正案，2026-09-17 运行前申报）

## 0. 定位与依据

- F4 参数集预登记过 swap_prob 敏感性（"注入配比 70% 替换 / 30% 翻转 `--swap-prob 0.7` CLI 化 + 申报"），
  k 族与 0.7 判据族交付后此列静默缩水；申请人 2026-09-17 决断补跑（audit §3.2⑦，不接受"计划有、交付无"第六次）。
- 与 ⑥ 同构：新实验、新种子、dated amendment、确认集结果已知后追加。**不触碰种子 20261015 的 run-once**；
  `four_arm_confirm/` 全程只读（0.7 参照数字从封存确认集提取）。
- **本族为敏感性族，不进任何判定族，不影响门 v2 判定（PASSED 不变）**。

## 1. 事前预期（逐字，运行前已在 audit §3.2⑦ 在案；运行后不得改写）

> "Prediction: the rule advantage decreases monotonically with swap_prob, since two of the three rules target
> structural/status violations. If Δε* at swap_prob = 0.95 remains within the CI of the 0.7 reference, the ordering
> claim in §VIII is supported; if it collapses toward the unconstrained baseline, the rule floor is conditional on the
> injected error composition and must be restated as such in Abstract, Results and Discussion."

依据：min_rules 三条规则中至少两条（栈一致性收束 R2、非法关闭修正 R3）针对状态/结构错误，swap（动作替换）
概率升高意味着更多结构类错误，规则优势预期随之衰减；最有信息量的点在 swap_prob→1，不在中段。
两种结论形态均已事前绑定处置（形态 A → ordering claim 获支持；形态 B → rule floor 在
Abstract/Results/Discussion 重述为条件化命题）。

## 2. 规格（照 §3.2⑦，实际执行逐条核对）

| 项 | 申报 | 执行 |
|---|---|---|
| swap_prob 网格 | {0.3, 0.5, 0.7, 0.9, 0.95}（0.7 为参照点而非端点） | 同（30 格 summary.json 逐格核验） |
| 链 | confirm_set_600 --use-all-rows（600 链，200/200/200） | 同 |
| 四臂 | no_rules / retry_selfreport / retry_oracle / min_rules | 同 |
| 判据 | --success-criterion 0.5 | 同 |
| ε 网格 | 26 点 0→0.50（引擎默认） | 同 |
| ρ | {0, 0.5, 0.9} | 同 |
| r | {0.2, 0.5} | 同 |
| k | 2 | 同 |
| replicates | 20 | 同 |
| 注入种子 | 20261020（新申报，不与任何既有种子重用） | 同 |
| bootstrap | 链级 B=9999、种子 20261021、pooled+分层、约定同门 v2 实现 | 同（直接 import bootstrap_eps_star 函数） |
| 规模 | 5 × 6 × 1,248,000 = 37,440,000 | 同（每格 per_run_results.csv 实测 1,248,000 行） |

脚本：`evidence/videocad/scripts/run_swap_sensitivity.sh`（引擎 CLI 透传）+
`evidence/videocad/scripts/analyze_swap_sensitivity.py`（bootstrap/判定）+
`evidence/videocad/scripts/validate_swap_path.py`（校验 a）。
输出：`evidence/videocad/notes/sensitivity_swap/`；per_run 大表留 `tmp/sensitivity_swap/`
（可经 runner 字节级复现）。引擎墙钟 10:27:07–10:43:52（6 并行，8 核），30/30 格完成；
bootstrap 分析墙钟约 4 小时（单进程顺序，保持与门 v2 相同的单 rng 流约定）。

## 3. 硬验证

- **a) 路径同一性**：runner 以原样参数调用权威引擎（--swap-prob 透传）→ swap 路径即引擎路径（按构造成立）；
  独立验证：两次直接引擎 CLI 调用（dev 种子 20261022，校验专用）per_run_results.csv / curve_summary.csv /
  eps_star.csv 逐字节相同；120 个随机 (chain, ε, replicate, arm) 三元组逐字段比对 **0 mismatch**。
  见 `notes/sensitivity_swap/validation_swap_path.json`。
- **b) 运行计数**：30 格 × 1,248,000（600 链 × 20 replicates × 26 ε × 4 臂）= 37,440,000，
  逐格实测行数 + summary.json inputs 核验。**通过**。
- **c) 家族内 0.7 格 vs 封存确认集 0.7 格**（comparison_family07_vs_confirm.csv）：
  - **pooled 全部通过 0.01 阈**：|diff| = 0.0077–0.0092（6 格），与 k 族先例量级一致（~0.005）；
  - **分层 low 层 6 格超 0.01 阈（0.0142–0.0177），medium/high 全部 <0.009**，排查如下：
    差异来源是双随机源不同（注入种子 20261020 vs 20261015 改变每链每 replicate 的注入序列；
    bootstrap 种子 20261021 vs 门种子改变重抽流），在 n=200 层内的正常波动范围；family 与 confirm
    的 CI 大幅重叠，无路径/参数实现差异的可能（路径同一性已由 a 按构造 + 确定性验证成立；
    且本族内 r=0.2 与 r=0.5 在 ρ=0.9 下 Δε* 逐位相同，与确认集的 r-invariance 结构一致，交叉印证）。
    判定：抽样差，非实现差异；如实申报超阈格。
- **d) bootstrap 零删失核查**：**不成立（这是本族的实质发现之一，非缺陷）**。
  - 引擎 eps_star 层面：30/360 行 right_censored，全部为 min_rules，集中在 sp≥0.9
    （sp=0.9：low+medium；sp=0.95：全三层；pooled 同步右删失）；no_rules/retry 自报/oracle 零删失。
  - bootstrap 层面：42/120 格 pct_undefined > 0（其中 sp≥0.9 的 pooled/low/medium 格多数
    B_defined=0，即 9999 次重抽中 Δε* 全部无定义；sp=0.9, ρ=0.9 pooled 有 1/9999 次有定义）。
  - 机制：sp≥0.9 时 min_rules 在 26 点 0→0.50 全网格成功率不跌破 0.5 判据（ε=0.50 处 pooled
    成功率 0.523 @0.9、0.659 @0.95）→ ε*(min_rules) > 0.50，Δε* 右删失，以
    **下界 Δε* > 0.50 − ε*(retry_oracle)** 报告（verdict_AB.csv delta_lower_bound_if_censored）。

## 4. headline：pooled Δε* 轨迹（min_rules − retry_oracle，B=9999，种子 20261021；headline_pooled.csv）

r=0.2（主对照）：

| swap_prob | ρ=0.0 | ρ=0.5 | ρ=0.9 |
|---|---|---|---|
| 0.3 | −0.096002 [−0.100407, −0.091296] | 0.024999 [0.021103, 0.029298] | 0.062016 [0.057636, 0.067022] |
| 0.5 | −0.062336 [−0.068977, −0.055419] | 0.058665 [0.052373, 0.065] | 0.095682 [0.088658, 0.10262] |
| 0.7（族内参照） | 0.007342 [−0.003088, 0.019521] | 0.128343 [0.118534, 0.139837] | 0.165361 [0.154517, 0.177753] |
| 0.9 | 右删失（下界 > 0.322453） | 右删失（下界 > 0.443454） | 右删失（下界 > 0.480472） |
| 0.95 | 右删失（下界 > 0.322453） | 右删失（下界 > 0.443454） | 右删失（下界 > 0.480472） |

r=0.5 同构（见 bootstrap_swap_r05.csv）：ρ=0.9 与 r=0.2 逐位相同；ρ=0.5 各点差 ≤3.2×10⁻⁴；
ρ=0 差较大（−0.168/−0.134/−0.065）——与确认集的 r-invariance 结构（ρ≥0.5 不变、ρ=0 受预算影响）一致。

分解（aux_min_rules_minus_no_rules.csv）：ε*(min_rules) pooled = 0.0815 / 0.1152 / 0.1849
（sp=0.3/0.5/0.7，与 ρ 无关——注入决定）；ε*(retry_oracle) = 0.1775 / 0.0565 / 0.0195
（ρ=0/0.5/0.9，与 sp 无关）；ε*(no_rules) ≈ 0.0172 恒定。Δε*(sp) 随 sp 上升完全由 min_rules
ε* 右移驱动；Δε*(min_rules − no_rules) 沿 defined 前缀 0.064 → 0.098 → 0.168 单调增大，
**无任何塌向无约束基线的迹象**。

## 5. 0.7 族内参照 vs 封存确认集（校验 c，见 §3c；comparison_family07_vs_confirm.csv）

pooled 24 格中 6 格（2 r × 3 ρ）|diff| 0.0077–0.0092 全部 <0.01；分层 low 层 6 格 0.0142–0.0177
超阈（排查结论：种子双随机源的正常层内波动，CI 重叠，非实现差异——详见 §3c）。

## 6. 形态 A/B 判定（逐字句事前绑定；verdict_AB.csv）

逐字句的两个前提在 6/6 格（2 r × 3 ρ，pooled）**均不成立**：

- **形态 A 不成立**：swap_prob=0.95 的 Δε* 不在 0.7 参照 CI 内——但不是塌缩，而是**右删失于参照 CI 之上**
  （下界 0.32–0.48，参照 CI 上界最高 0.185）。
- **形态 B 不成立**：Δε* 未塌向无约束基线（min_rules − no_rules 在 defined 前缀单调增大至 0.168，
  0.95 处仍 > 0.32 下界），rule floor **没有**因注入构成条件性失效。

**判定：neither（6/6 格）**——事前预期方向（单调衰减）被证伪，实际方向相反：
**Δε* 随 swap_prob 单调上升**（defined 前缀所有步长为正），且在 sp→1 端 min_rules 强到
全网格不达 0.5 判据（ε* > 0.50 右删失）。按零编造纪律如实报告，事前预期句不改写；
两种事前绑定的处置（A：ordering claim 获支持 / B：rule floor 条件化重述）**均不触发**——
§VIII ordering claim 的方向性陈述（如含"swap 升高→规则优势衰减"类表述）须按实际方向修正，
而 rule floor 相反地获得加强证据：规则优势对注入构成的变化方向与事前预期相反，
结构/状态类错误占比升高时规则优势不减反增（与 R2/R3 针对结构类错误的机制解读一致：
动作替换保持状态可读、可被规则检出并修复，状态翻转不可修复）。
主格（r=0.2, ρ=0.9, pooled）：Δε*(0.95) 右删失，下界 > 0.480472，0.7 参照 CI
[0.162112, 0.184894]，verdict = neither。其余 5 格同为 neither（分层证据见
bootstrap_swap_r02/r05.csv 各层行）。

## 7. 单调性判定（事前预期：单调衰减——**证伪**）

- 事前预期"rule advantage decreases monotonically with swap_prob"：**不成立**。
- 实际：6/6 格 defined 前缀（0.3→0.5→0.7）**单调上升**，步长 +0.0337 / +0.0697
  （所有格一致；由 ε*(min_rules) 对 sp 单调右移、ε*(retry) 与 sp 无关所致），
  0.7→0.9 步长 ≥ 0.315（右删失下界）——上升在加速。
- **非单调格：无**（不存在任何下降步长或震荡；"非单调"以相反方向成立）。
- monotonicity_pooled.csv（6 行；原输出含遍历 bug 导致的重复行，已去重，见 §8）。

## 8. 偏离规格记录

- **无规格偏离**（网格/种子/参数/规模全部照 §3.2⑦ 执行）。
- 过程修正（均不影响数据）：
  1. runner 初版未预建格目录导致日志重定向失败、首轮 30 格空转（引擎未执行即退出，无任何输出文件）；
     修正为 run_cell 内先 `mkdir -p` 后重跑。首轮未产生任何数据文件，不存在部分写入或重用。
  2. 分析脚本初版目录名格式化 bug（rho0.0 → rho0），在任何数据读入前崩溃，修正后重跑；
     bootstrap 从头完整执行。
  3. 【运行后补记】monotonicity 遍历 bug 产生重复行（每 (r,rho) 重复 5 次、内容完全相同），
     已去重为 6 行并同步修正脚本（future-proof）；bootstrap CSV 与判定文件未受影响。
- 校验/dev 种子 20261022（validate_swap_path.py 与 timing probe）为运行前申报三种子
  （20261020/20261021）之外新增的校验专用种子，与所有既有种子（20260915/20260916/20261015–20261019）
  及本族种子不重用，仅用于校验小样运行（输出即删，可复现），不进入任何结果数据。
- summary.json 中两条【运行后补记】declaration（无增量落盘/进度输出的事实申报、monotonicity
  去重申报）为运行结束后直接编辑补入，数值字段零改动。

## 9. 流程改进（申请人 2026-09-17 指令，记入备考；下一敏感性族开跑前必须修，改动量两行级）

1. **增量落盘**：analyze 类脚本必须每格算完立即落盘（incremental write），不得把全部输出积压到
   main() 末尾一次性写出——本次约 4 小时计算在完成前没有任何可恢复中间产物，第 29 格死与
   第 1 格死损失相同。本族脚本无增量落盘，已在 summary.json declarations 如实申报。
2. **进度输出**：每格打一行进度（cell 序号 / 30 + 耗时）到 stdout，杜绝盲跑。
3. **进度监测口径更正**（供后续复查参照）：用 rchar 判断停滞会误报——脚本"读一格 → 算数分钟 →
   读下一格"，格内计算期 rchar 完全平坦属正常态；正确指标是 /proc/PID/stat 的 **utime 增量**
   （计算期持续走）。且 rchar 摸到 3.0 GB 时最后一格才刚读完、仍有完整一格计算 + 末尾写盘，
   不得在该点判异常。本次收尾轮询已改用 utime（utime 1395117 ticks ≈ 3.9 h CPU，与墙钟一致）。

## 10. 文件清单（evidence/videocad/notes/sensitivity_swap/）

- 脚本：scripts/run_swap_sensitivity.sh、scripts/analyze_swap_sensitivity.py、scripts/validate_swap_path.py
- per-cell：sp{0.3,0.5,0.7,0.9,0.95}_r{0.2,0.5}_rho{0,0.5,0.9}/（curve_summary.csv、eps_star.csv、
  summary.json、引擎日志；per_run_results.csv ~1.1 GB × 30 留 tmp/sensitivity_swap/，可字节级复现）
- 汇总：bootstrap_swap_r02.csv、bootstrap_swap_r02_replicates.csv、bootstrap_swap_r05.csv、
  bootstrap_swap_r05_replicates.csv、headline_pooled.csv、aux_min_rules_minus_no_rules.csv、
  comparison_family07_vs_confirm.csv、monotonicity_pooled.csv、verdict_AB.csv、
  eps_star_censor_check.csv、validation_swap_path.json、summary.json
