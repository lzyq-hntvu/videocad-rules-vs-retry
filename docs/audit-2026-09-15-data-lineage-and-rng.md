# 数据血缘与随机数审计 · 2026-09-15

> 触发：全量开跑前审查发现 2 个会毁掉结果的问题 + 1 个数据来源问题。
> 本文件是实验方案 v1 的**操作修正案**：方案原文（docs/experiment-plan-v1.md）不动，冲突处以本文件为准。
> 所有证据可在本仓库按文中命令复现。

## 结论速览

| # | 发现 | 严重度 | 处置 | 状态 |
|---|---|---|---|---|
| F1 | `data/preliminary_results.json` 不是管线产物，是照 0.7 阈值反推的手工曲线 | 🔴 | 撤回隔离，禁用两个消费它的作图脚本，任何图表不得引用 | ✅ 已处置 |
| F2 | 旧管线随机数由顺序推进母发生器导出，扩展/重排即静默破坏配对 | 🔴 | 新引擎确定性种子 + 预生成定长误差向量全臂共享 + 重试独立流 | ✅ 已处置 |
| F3 | 规则臂读取 ground truth；且旧管线**全臂共用**的 mismatch-budget 判死也读 gt | 🟠 | 新引擎成败定义零 gt；oracle 通道清单申报；mismatch 仅作分析量 | ✅ 已处置 |
| F4 | 三个未申报自由参数（0.12 阈值 / 0.7:0.3 配比 / 栈非空判死） | 🟡 | 全部 CLI 化 + summary.json 申报；0.12 判定移出成败路径 | ✅ 已处置 |
| F5 | `rules_retry` 结构性退化为 `min_rules` 的同义词（代码可证 + 实证） | 🟠 | **已决议：选 C**——四臂，退化验证降级为方法句（§二轮 2.1） | ✅ 已处置 |

---

## F1 · preliminary_results.json 不是管线产物 🔴

**证据**（全部本地可复现）：

1. **物理不可能性（最硬）**：本管线 ε=0 时零注入，no_rules 成功率必为 1.0。JSON 在 ε=0 报 low 0.95 / medium 0.88 / high 0.79（两臂同）——任何参数组合下都不可能产生。
2. **六点精确命中**：JSON 的 6 个 ε\*（low 0.04/0.08、medium 0.02/0.06、high 0.02/0.04）全部落在 success_rate **恰好等于 0.70** 的格点上（`data/quarantine/preliminary_results.json.withdrawn` 可直接核对）。
3. **判据两套**：JSON `"success_threshold": 0.7`；脚本 `run_h2_h3_mechanism_proxy.py:162` 硬编码 `success < 0.5`。
4. **网格两套**：JSON 5 点（0→0.08 step 0.02）；脚本默认 11 档（0→0.20 step 0.02）。
5. **日期**：JSON `created: 2025-03-03`，早于本仓库任何实验活动。

**管线自身是清白的**：同参数重跑旧脚本，与已入库输出**逐字节一致**——

```bash
python3 evidence/videocad/scripts/run_h2_h3_mechanism_proxy.py --out-dir tmp/dev_repro_old
diff tmp/dev_repro_old/curve_summary.csv evidence/videocad/notes/h2_h3_proxy_experiment/curve_summary.csv  # → 空
diff tmp/dev_repro_old/per_run_results.csv evidence/videocad/notes/h2_h3_proxy_experiment/per_run_results.csv  # → 空
```

`notes/h2_h3_proxy_experiment/` 的两臂结果是真的；**只有 JSON 是假的**。这也解释了本子 0.5/0.7 矛盾：正文抄脚本口径，图 6 画的是这个手工文件。

**JSON vs 真实管线**（重叠格点，success_rate）：

| label | ε | JSON no_rule | 真实 no_rules | JSON min_rule | 真实 with_rules |
|---|---|---|---|---|---|
| low | 0.02 | 0.88 | 0.6183 | 0.92 | 0.7825 |
| low | 0.04 | 0.70 | 0.3783 | 0.85 | 0.6567 |
| medium | 0.02 | 0.70 | 0.4225 | 0.82 | 0.7700 |
| high | 0.02 | 0.70 | 0.2417 | 0.76 | 0.6925 |

JSON 系统性地比真实 no_rules 乐观 0.2–0.45。若拿它当基线，"规则抬升阈值"会被夸大近一倍。

**附带**：JSON 的 H1 段 low（−0.1035/−0.0950）与本子 p.16 所述 high 子集数值相同，low/high 很可能标反；high 段的 improvement 为负（−0.0075）。H1 不在本文范围，不再深挖。

**处置**：
- 文件移入 `data/quarantine/preliminary_results.json.withdrawn`，附撤回说明；**任何图表、论文、本子回填不得引用**。
- `scripts/plot_h1_results.py`、`scripts/plot_h2h3_results.py` 已改为运行即退出并提示（它们读的就是这个 JSON）。
- 方案 v1 步骤四**方向修正**：脚本本来就用 0.5，要改的不是判据，是停用 JSON。0.5 保持，插值 + bootstrap 照加。
- 本子 p.16 那组 ε\* 不可再用；论文中的历史对照一律引用 `notes/h2_h3_proxy_experiment/`（两臂）或新五臂输出。

## F2 · 随机数方案会让配对设计静默失效 🔴

**证据**：`run_h2_h3_mechanism_proxy.py:271` 起——`rng_master = random.Random(args.seed)`，种子按 (ε, chain, rep) 循环顺序 `randint` 依次消耗。

1. 加臂、改循环嵌套 → 全部种子平移 → 跨运行不可比。
2. 若重试臂在模拟内部惰性抽样（旧 `perturb_events` 模式），重试消耗随机数 ≠ 规则臂 → 同一 (chain, ε, rep) 下各臂误差流在首次重试后分叉，**配对静默失效且无报错**。

**处置**（新引擎 `run_five_arm_experiment.py`）：
- 初始误差向量：种子 `sha256(seed,"inj",chain_id,rep)`，预生成长为 L 的**定长三元组数组**；corrupt 判定为 `u < ε`，**ε 不参与抽样** → 同一组数组服务全部 5 臂 × 全部 ε 档（跨臂 + 跨 ε 双重配对）。
- 重试重抽：独立流 `sha256(seed,"retry",chain_id,rep,step,attempt)`，与主向量完全隔离。
- 无顺序推进母发生器：增删臂、调整循环顺序**不改变任何已有结果**。
- 已验证：同参数两次运行 `per_run_results.csv` **逐字节一致**（sort 后 diff 为空）。

## F3 · 规则臂读取 ground truth（审查发现）+ 全臂共用判死也读 gt（审计补充）🟠

**证据**：
- `min_rules` 修复①：`run_h2_h3_mechanism_proxy.py:108` `obs["status"] = gt["status"]`——唯一读 gt 的规则（另两条：投影到栈顶、空栈转 started，均不读 gt）。本误差模型下注入器只产出 started/finished，该分支实为死代码，但口径保留并申报。
- **审计补充**：`run_h2_h3_mechanism_proxy.py:138` `mismatch_rate > mismatch_rate_threshold` 判死在所有臂（含 no_rules）内比较 `obs vs gt`——**每个臂的成败都掺了 oracle 信息**，审查报告未覆盖此条。

**影响量化**（开发集，legacy with_rules vs 新引擎 min_rules，ε=0.02）：0.7825 → 0.9317——旧"with_rules"被这条隐藏判定压掉了约 0.15 的成功率。

**处置**（新引擎）：
- 成败定义 = 无步放弃 + 无环境错误终止 + 结束栈空。**零 gt**。
- mismatch 统计照常输出，仅作分析量（传播增益 G 的原料），不参与成败。
- oracle 通道清单（两条死代码说明 + retry_oracle 判定 + 已移除项）写入 `summary.json design_notes.oracle_channels`，即论文 Section III 的申报素材。
- 结论只从 oracle-vs-oracle（min_rules vs retry_oracle）对比中取；retry_selfreport 作无 oracle 下界。审查"歪打正着"的判断成立，现有了原则性理由。

## F4 · 三个未申报自由参数 🟡

| 参数 | 旧值 | 新引擎处置 |
|---|---|---|
| `--mismatch-threshold` | 0.12 | **移出成败路径**（见 F3）；不再作为自由参数存在，无需敏感性（本身就是 gt 判定） |
| 注入配比 | 70% 替换 / 30% 翻转 | `--swap-prob 0.7` CLI 化 + 申报 |
| 结束栈非空判死 | 硬编码 | 写入 design_notes.success_definition 申报（语义不变） |
| （新增申报）预算公式 | 无 | B = ceil(L×(1+r))，每次尝试含未通过检定者计 1，五臂同 B |
| （新增申报）步放弃 | 无 | k+1 次尝试未过 → 放弃该步不施加，链记 abandoned，继续向下走 |

敏感性表（论文表 3）参数集：主判据 0.5 / 敏感性 0.7（`--success-criterion`）、k ∈ {1,2,3}（`--k`）、r ∈ {0.2,0.5}（`--budget-ratio`）、swap_prob（`--swap-prob`）。

## F5 · rules_retry 结构性退化 🟠 —— 待决策

**代码可证**：`min_rules` 修复后（finish 投影到栈顶 / 空栈转 started），执行按构造不抛环境错误 → `rules_retry = min_rules + retry_selfreport` 的重试分支永不触发 → 两臂恒等。

**实证**：开发集 90 链 × 11 ε × 40 rep = 39,600 对 per-run 结果，**全部相同**（success、fail_reason、attempts_made 逐一相等）。

这本身合法地回答了方案"互补还是冗余"——答案是**冗余**。但预登记锁死前，申请人需知情选择：

- **A（默认，忠实方案）**：保留五臂，如实报告 rules_retry ≡ min_rules，作为"修复已覆盖环境可检错误"的结构性证据。
- **B**：改定义为 `min_rules + retry_oracle`（修复 + 完美检测重试），组合臂获得非退化语义，但与方案表 A 原文不符，需在预登记中明示修正。
- **C**：移除该臂，主实验降为四臂。

## 新引擎开发集输出（90 链 × 11 ε × 40 rep × 5 臂 = 198,000 runs，18.3s ≈ 0.09ms/run）

success_rate 摘录（k=2, r=0.2, seed=20260226；全表见 tmp/dev_five_arm/curve_summary.csv）：

| label | ε | no_rules | retry_self | retry_oracle | min_rules | rules_retry |
|---|---|---|---|---|---|---|
| low | 0.02 | 0.6217 | 0.7958 | 1.0000 | 0.9317 | 0.9317 |
| low | 0.08 | 0.1467 | 0.3883 | 0.9700 | 0.7808 | 0.7808 |
| medium | 0.04 | 0.1858 | 0.4517 | 0.9983 | 0.8358 | 0.8358 |
| high | 0.04 | 0.0700 | 0.2533 | 0.9958 | 0.6975 | 0.6975 |
| high | 0.12 | 0.0008 | 0.0175 | 0.8408 | 0.4817 | 0.4817 |

读法（内部一致性检查全部通过）：
- 新 no_rules ≈ 旧 no_rules（同一模拟过程，不同随机流，差异在噪声内）✓
- min_rules > retry_selfreport > no_rules，retry_oracle 居首——臂间序合理 ✓
- retry_oracle 与 min_rules 的 ε\* 间距就是决策门要量的 Δε\*；开发集上三层均为正且可观 ✓
- 确认集 780,000 runs 预估 ~72s；消融 324,000 runs ~30s。计算预算再次确认无约束。

## 复现入口

```bash
# 旧管线 parity（4.1s，逐字节复现已入库输出）
python3 evidence/videocad/scripts/run_h2_h3_mechanism_proxy.py --out-dir tmp/dev_repro_old

# 四臂引擎（开发集口径；--retry-repro-prob 扫 ρ ∈ {0, 0.5, 0.9}）
for rho in 0.0 0.5 0.9; do
  python3 evidence/videocad/scripts/run_four_arm_experiment.py \
    --per-label 30 --replicates 40 \
    --eps-list 0,0.02,0.04,0.06,0.08,0.10,0.12,0.14,0.16,0.18,0.20 \
    --k 2 --budget-ratio 0.2 --retry-repro-prob $rho --seed 20260226 \
    --out-dir tmp/dev_four_arm_rho$(echo $rho | tr -d '.')
done
```

> 引擎原命名 `run_five_arm_experiment.py`（含退化臂），F5 决议 C 后更名为 `run_four_arm_experiment.py`。

---

## 二轮修正案（2026-09-15 下午，全量开跑前设计锁定）

### 2.1 F5 决议：四臂，方法句锁死

**决议：选 C**（移除 rules_retry，主实验四臂）。理由（申请人）：退化是定义的必然——min_rules 是全覆盖修复策略，"组合冗余"不是实证结论，写成 finding 会被审稿人误读为"规则与重试一般不互补"，反而成为扣分项；B（min_rules+retry_oracle）是真问题但属第二篇论文或 Discussion 一段，八页装不下。

**论文 Section III 方法句（预登记锁死，verbatim）**：

> `min_rules` is a *total* repair policy: every violation it detects, it corrects, so execution never raises and a retry layer placed on top is inert by construction. We verified this empirically (39,600/39,600 runs identical) and therefore report four arms rather than five.

既有的 39,600/39,600 验证保留为方法注记，不进入 Results。上一版样稿的 Results C 段作废。
引擎已更名 `run_four_arm_experiment.py`，`ARMS` 四元组，`design_notes.withdrawn_arm` 记录该句。

### 2.2 F6：ρ 规格修正——重试的误差相关性（本修正案的核心）

**责任归属**：方案 v1 表 B "with a fresh error draw at rate ε" 把重试设为最有利形态。算术验证：k=2 独立重抽下步失败概率 ε³（ε=0.04 时 6.4e-5），24 步链期望成功 ≈0.9985——与开发集观测 0.9958 吻合。**按旧规格主对比在开发集上已指向 null（0.996 vs 0.698），是规格缺陷而非重试的真实强度。**

**修正**：新增申报参数 ρ（`--retry-repro-prob`）= 重试复现主尝试同一误差的概率。
ρ=0 独立重抽（重试上界，最有利于重试）；ρ=1 重试完全无效。实现：重试流先抽 ρ 判定，复现或独立重抽均确定性。真实 GUI 感知类误差 ρ 高、执行/时序类低。

**开发集 ρ 扫描**（90 链 × 11 ε × 40 rep × 4 臂 × 3 ρ = 475,200 runs，约 100s；no_rules/min_rules 跨 ρ 逐 run 一致 = 0.00e+00，配对无副作用已验证）：

retry_oracle 的 ε\*（判据 0.5，插值；min_rules 对照：low/medium 在 0.20 网格顶仍 right_censored，high = 0.1112）：

| ρ | oracle low | oracle medium | oracle high | 规则 vs oracle |
|---|---|---|---|---|
| 0.0 | 0.1997 | 0.1810 | 0.1663 | low/medium 规则不输（censored >0.20），high oracle 胜 |
| 0.5 | 0.0923 | 0.0614 | 0.0356 | **三层规则全胜，Δε\* ≈ 0.08–0.16** |
| 0.9 | 0.0364 | 0.0201 | 0.0145 | **三层规则全胜，Δε\* ≈ 0.10–0.19** |

机制解读：ρ≥0.5 时重试收敛从几何级（ε³）退化为近线性（≈ερᵏ），预算 B 还被重试消耗放大——高 ε 处 oracle 因 budget_exhausted 提前出局（这正是共享预算约束的设计意图）。

**论文 headline 由此从"规则赢/输"升级为"重试何时够用，取决于误差的可重复性 ρ"**——直接回应评审 3 的"可解释、可量化的误差—风险关系"，也是本文脱离"又一个消融实验"的增量所在。

**决策门需按 ρ 重新表述（待申请人锁死，建议稿）**：

```
对每个 ρ ∈ {0, 0.5, 0.9}：Δε*(min_rules − retry_oracle) 的 95% CI（链级 bootstrap）
若全部 ρ 的 CI 都跨 0 → 任何误差形态下规则都无增量 → 停止投稿
若存在 ρ 区间 CI 全正 → 该区间即规则的价值域，论文主结论
```

即：决策门从"单次二元判定"变为"对 ρ 区间的存在性判定"。这比原门更弱（更易通过）但更诚实——它与修正后的论文主张一致。

### 2.3 审计补笔 1（F1 加固）：ε=0 的实证值

F1 的"ε=0 时成功率必为 1.0"依赖"gt 链全部良构（结束栈空）"这一前提。现直接给出实证：**已入库真实输出与新四臂引擎在 ε=0 处、全部臂 × 全部复杂度层，成功率 = 1.0000**（逐字节 parity 一致）。前提对开发集 90 链成立；确认集 600 链跑批时应将此检查加入 sanity（ε=0 行必须全为 1.0）。

### 2.4 审计补笔 2（F3 独立成段）：旧 no_rules 基线也是 gt 基线

`mismatch_rate > 0.12` 判死位于旧 `simulate_chain` 主循环，**no_rules 与 with_rules 同样命中**——它每步比较 obs 与 gt，累计失配率超阈值即判死。因此：

- 旧管线的"无规则"基线**并非无信息基线**：它内置了一个 gt 失配预算监控。旧两臂输出的解释必须附带此限定。
- 该判定同时是旧 with_rules 被压低约 0.15 的机理（见 F3 量化），两条通道（规则修复读 gt + 全臂判死读 gt）在旧管线里叠加。
- 新引擎将成败定义清零 gt（判死移除，mismatch 仅作分析量），no_rules 才是真正无信息下界。跨口径引用旧输出时只能作"带 gt 监控的旧语义"下的对照。
