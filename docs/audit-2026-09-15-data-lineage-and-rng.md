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
| F5 | `rules_retry` 结构性退化为 `min_rules` 的同义词（代码可证 + 实证） | 🟠 | **待申请人决策**（预登记锁死前）：保留报冗余 / 改定义 / 移除 | ⏸ 待决策 |

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

# 新五臂引擎（开发集口径）
python3 evidence/videocad/scripts/run_five_arm_experiment.py \
  --per-label 30 --replicates 40 \
  --eps-list 0,0.02,0.04,0.06,0.08,0.10,0.12,0.14,0.16,0.18,0.20 \
  --k 2 --budget-ratio 0.2 --seed 20260226 --out-dir tmp/dev_five_arm
```
