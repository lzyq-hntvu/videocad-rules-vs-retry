# videocad-rules-vs-retry

> 规则约束是否真的优于朴素重试？—— VideoCAD 符号动作链上的受控误差注入模拟研究
>
> 实验方案 v1 见 [docs/experiment-plan-v1.md](docs/experiment-plan-v1.md)，本文件只做入口与地图。

## 项目由来

国自然面上申请书 6267076144（复杂 GUI 多步骤任务中的视觉可靠性机制研究）未获资助。
本仓库把其中的 H2/H3 代理实验收敛为一篇可发表的单问题实证研究：**先做实验，再写论文**。
实验管线、数据底座、证据台账全部复制自 `~/projects/archived/nsfc-general-2026`，
相对路径与 CSV 内路径保持不变，脚本零改动可跑。

目标会议：MiTA 2027，截稿 2026-10-15。投不投由第 2 周末的决策门定，不在现在定。

## 范围声明（论文标题、摘要、Limitations 三处必须这样写）

这是一项在 **VideoCAD（Onshape 浏览器 CAD 录制）派生动作链**上的受控误差注入**模拟研究**。

- **本文主张**：在符号动作链层面，规则约束相对朴素重试的增量、及其随复杂度与误差类型的变化。
- **本文不主张**：对真实视觉 GUI 智能体的评测结论。图像侧感知闭环未完成、元素框级定位误差未验证、
  `qa.json` 三方映射未恢复——三条写进 Future Work，不藏。

## 单一研究问题

> 在多步骤动作链上注入受控误差后，规则约束相对于朴素重试是否存在可重复的增量？
> 该增量在哪些复杂度层与误差类型上成立，在哪些条件下消失？

## 预先登记的决策门 v2（2026-09-15 三轮修正锁死，替代方案 v1 原门；拿到结果后不得修改）

```
主检验格：ρ = 0.9，三层合并（确认集 600 链合并曲线，链级 bootstrap B = 1000）
若 Δε*(min_rules − retry_oracle) 的 95% CI 跨 0
→ 停止投稿

次要分析：ρ ∈ {0, 0.5} × 三层共 9 格，Holm 校正，全部如实报告
铁律：次要格全正不构成析取逃生通道——主格不显著即按阴性主结果报告
```

开发集主格预览 Δε\* = **+0.1767**；规则价值随误差可重复性单调显现（ρ=0 → +0.017，ρ=0.5 → +0.138，ρ=0.9 → +0.177，审计 §3.5）。

负结果也是干净的结果：它直接指明下一轮选题方向，且是在花掉 6300 元注册费之前知道。

## 目录地图

```
videocad-rules-vs-retry/
├── docs/
│   └── experiment-plan-v1.md        # 实验方案 v1 全文（范围、四步骤、决策门、排期、分工）
├── evidence/videocad/
│   ├── scripts/                     # 实验管线（8 个脚本，全部 stdlib 起步）
│   │   ├── run_h2_h3_mechanism_proxy.py      # 核心：误差注入 + 规则抑制模拟（本论文的主引擎）
│   │   ├── run_h1_domain_shift_proxy.py      # H1 图像域代理（需 numpy+PIL+图像，本文不引用）
│   │   ├── build_cad_action_overlap_sample_pool.py   # 135 条联动样本池
│   │   ├── label_action_complexity_and_sample.py     # 复杂度标签与分层抽样
│   │   ├── analyze_action_pairing_and_complexity.py  # 动作配对与复杂度指标
│   │   ├── inspect_action_json.py / probe_cad_imgs_mapping.py / build_videocad_evidence_manifest.py
│   ├── notes/                       # 派生数据与既有实验输出（样本池 CSV、复杂度指标、
│   │                              #   h1/h2_h3 代理实验结果、证据台账 Day2–Day7）
│   ├── logs/                        # Day1–Day9 探查与实验日志
│   └── samples/dataverse/
│       ├── action_json_unpacked/action_json/   # 数据底座：44,291 条动作链（已核实文件数）
│       ├── qa.json                  # QA 三方映射（本文未恢复，Future Work；5MB 一并复制备查）
│       └── readme.md
├── scripts/                         # 结果作图（plot_h1/h2h3_results.py + utils.py，需 matplotlib）
├── data/preliminary_results.json    # 本子预实验结果（H1/H2/H3 既有数值，供对照）
└── tmp/                             # 冒烟测试与临时输出（git 忽略）
```

刻意**未**复制（留在 `archived/nsfc-general-2026`，需要时去取）：

| 未复制内容 | 原因 |
|---|---|
| `cad_imgs.zip`（967M） | 图像侧不在本文范围（范围声明）；H1 脚本如需图像从旧仓库读 |
| `action_json.zip`（23M） | 与 `action_json_unpacked/` 冗余 |
| `proposal/`、`docs/` | 国自然申报书文本，非实验内容；出处页码见方案 v1 末节 |
| `evidence/literature/`（论文 PDF） | 写论文阶段再读，旧仓库可取 |
| `paperbanana/`、`figures/`、`skills/` | 写作工具与申报书插图，论文阶段再说 |

## 快速开始

```bash
cd ~/projects/videocad-rules-vs-retry

# 冒烟测试：3 链/层 × 2 重复 × 3 个 ε 点，秒级完成，输出到 tmp/
time python3 evidence/videocad/scripts/run_h2_h3_mechanism_proxy.py \
  --per-label 3 --replicates 2 --eps-stop 0.04 \
  --out-dir tmp/smoke_h2h3

# 开发集全量复现（90 链 × 40 重复 × 11 ε 档，历史两臂）：
python3 evidence/videocad/scripts/run_h2_h3_mechanism_proxy.py

# 四臂引擎 ρ 扫描（开发集；约 100 秒跑完全部 3 档）：
for rho in 0.0 0.5 0.9; do
  python3 evidence/videocad/scripts/run_four_arm_experiment.py \
    --per-label 30 --replicates 40 \
    --eps-list 0,0.02,0.04,0.06,0.08,0.10,0.12,0.14,0.16,0.18,0.20 \
    --k 2 --budget-ratio 0.2 --retry-repro-prob $rho --seed 20260226 \
    --out-dir tmp/dev_four_arm_rho$(echo $rho | tr -d '.')
done

# 作图（注意：plot_h1/h2h3_results.py 因数据源撤回已禁用，见数据红线）
python3 scripts/plot_h2h3_results.py   # → 退出并指向真实数据源
```

环境：Python 3.12（WSL2 系统 Python 即可，numpy / PIL / matplotlib 已装）。
核心模拟脚本只依赖标准库，matplotlib 缺失时自动跳过作图不报错。

## 四臂定义（方案 v1 表 A + 二轮修正案；F5 已决议选 C，预登记锁死）

| 标识 | 定义 | 角色 |
|---|---|---|
| `no_rules` | 无约束，误差注入后直接执行 | 下界（✅ 旧管线已有对应臂） |
| `retry_selfreport` | 环境判非法（栈下溢/finish 失配，不读 gt）才重试该步，每步至多 k 次 | 现实重试基线（✅ 新引擎） |
| **`retry_oracle`** | 偏离预期状态转移（attempt ≠ gt event）即重试（完美检测），每步至多 k 次 | **主对照**（✅ 新引擎） |
| `min_rules` | 栈一致性收束 + 非法关闭修正（含一处 gt 修复声明，oracle 级信息） | 待检验项（✅ 旧口径保留） |

> ~~`rules_retry`~~ **已移除**（F5 选 C）：min_rules 是全覆盖修复策略，叠加的重试层恒为惰性——39,600/39,600 runs 实证。方法句锁死见审计 §2.1。
> 第五臂的余留问题（"oracle 检测叠加在修复之上"）归第二篇论文或 Discussion。

**申报参数**（全部 CLI 化，进 summary.json）：k（默认 2，敏感性 {1,3}）、r（默认 0.2，敏感性 {0.5}，**承重项**：ρ=0 处 Δε\* 随 r 变号，正文必须报，审计 §3.3）、
swap_prob（0.7）、**ρ `--retry-repro-prob`（默认 0，扫描 {0, 0.5, 0.9}）**、判据 0.5（敏感性 0.7）。
ρ = 重试复现同一误差的概率：**ρ=0 对应瞬时/执行类误差（时序、竞态、点击抖动）——真实误差类，非稻草人**；ρ→1 对应可重复误差（感知类）。
**论文主张定稿：规则对可重复误差有价值；对瞬时误差，预算充足时重试已经足够**（审计 §3.4；ρ=0 结论必须与 r 条件同引——§3.3 的预算归因）。
ε 网格：开发集与确认集统一 26 档 0→0.50 step 0.02（方案 v1 的 0.15 上限作废，审计 §3.1）。

**主断言必须对 `retry_oracle` 成立。** 只赢过 `retry_selfreport` 就如实写成较弱结论。

# ⚠ 数据红线（2026-09-15 审计，详见 [docs/audit-2026-09-15-data-lineage-and-rng.md](docs/audit-2026-09-15-data-lineage-and-rng.md)）

- **`data/preliminary_results.json` 已撤回隔离**至 `data/quarantine/`——它不是管线产物（ε=0 时成功率物理上不可能 <1；六个 ε\* 全部恰好命中 0.70 格点；判据 0.7 vs 脚本 0.5）。**任何图表、论文、本子回填不得引用。** 真实两臂输出在 `evidence/videocad/notes/h2_h3_proxy_experiment/`（同参数重跑逐字节一致，已验证）。
- 正式实验一律用 **`run_four_arm_experiment.py`**（配对随机数、成败定义零 gt、ρ 误差相关性、参数全申报）；旧 `run_h2_h3_mechanism_proxy.py` 仅作历史两臂对照（其 no_rules 基线内含 gt 监控，见审计补笔 2）。
- ~~`rules_retry ≡ min_rules` 结构退化已实证（39,600/39,600 全同），处置待决策~~ → **F5 已决议选 C**：臂已移除，验证降级为方法句（审计 §2.1）。

## 既有实验输出（真实管线产物，可引用）

- `evidence/videocad/notes/h2_h3_proxy_experiment/` — 90 链 × 40 重复 × 11 ε，no_rules vs with_rules 两臂结果与图（parity 已验证）
- `evidence/videocad/notes/h1_proxy_experiment/` — H1 域移位代理结果（H1 不在本文范围）
- 新五臂开发集输出 — `evidence/videocad/notes/five_arm_dev/`（90 × 40 × 11 ε × 5 臂的结论件；per_run 大表可一键再生成，见审计末节；确认集跑批后入 `notes/five_arm_confirm/` 并打 tag）

> 注意：旧两臂输出的 ε\* 取格点值——方案 v1 步骤四（插值 + 链级 bootstrap CI）正是为此，新实验一律用新口径。旧输出的 with_rules 臂被已移除的 gt 判定（mismatch-budget 0.12）压低约 0.15，跨口径比较时见审计 F3 量化。

## 状态

- [x] 项目搭建、实验内容复制、管线冒烟（2026-09-15）
- [x] 实测单次耗时：≈0.1 ms/run（3,300 runs 计时通过 1.6s，含约 1.3s 固定启动）→
      全量 1,104,000 runs 纯模拟约 2–3 分钟，加 I/O 也在小时级以内。
      **不需要回调重复数或链数**（方案表 D 的预案不触发）
- [x] **数据血缘与 RNG 审计**（2026-09-15，docs/audit-2026-09-15）：伪造 JSON 撤回隔离、
      四臂新引擎（配对随机数 + 成败定义零 gt + 参数全申报）、旧管线 parity 逐字节验证通过、
      开发集 sanity 全过
- [x] **F5 决议（选 C）**：rules_retry 臂移除，退化验证（39,600/39,600）降级为 Section III 方法句，预登记锁死
- [x] **ρ 误差相关性参数**：`--retry-repro-prob`，开发集扫描 {0, 0.5, 0.9}——
      ρ=0 时主对比指向 null（规格缺陷证据），ρ≥0.5 时规则三层全胜；
      论文 headline 升级为"重试何时够用取决于误差可重复性 ρ"
- [x] LICENSE（MIT）
- [x] **决策门 v2 锁死**（审计 §3.2）：主检验格 ρ=0.9 三层合并；次要 9 格 Holm、全报、无析取逃生
- [x] **A 删失消除**：网格延至 26 档 0→0.50，18 个 ε\* 全部非删失；确认集网格同步修正（§3.1）
- [x] **C 预算归因**：analyze_fail_mix.py；ρ=0 处 oracle 失败 46–76% 是预算耗尽，Δε\* 随 r 变号 → r 敏感性升为承重项；ρ≥0.5 预算占比≈0，规则优势非伪影（§3.3）
- [x] **D ρ=0 机制定性**：瞬时/执行类误差（时序、竞态、点击抖动），真实误差类非稻草人；论文主张定稿"规则对可重复误差有价值，瞬时误差预算充足时重试已够"；ρ=0 结论与预算绑定表述已锁（§3.4 复查项 4）
- [x] **复查四项闭环**（2026-09-16）：①`--eps-list` 默认改 26 档 + `run_confirmation.sh`/`Makefile` 固化全参 ②`bootstrap_eps_star.py` 先于确认集写就，开发集验证主格 CI [0.157, 0.200] 全正、9 格零删失 ③次要族 9 格 Holm 与 p 值定义预登记进 §3.2 ④ρ=0 预算绑定表述四处同步
- [x] **二批复查闭环**（2026-09-16）：①对照量 Δε\*(oracle−no_rules) 预登记——开发集 ρ=0.9 时 ≈0.0022 ≈ 0，主格"重试近惰性"机制实锤，按预登记句式进正文 ②§3.2 三段式消歧（主检验/次要族/描述性）③B=9999（p 分辨率下限 2×10⁻⁴ 已声明）④**确认集 600 链已抽样**（`make sample-confirm`，种子 20260916，排除开发 135，200/200/200，逐字节确定性已验）
- [x] **门 v2 已批准**（胡宇明，2026-09-16，批准时确认集尚未解封）；运行种子 **20261015** 预登记入 §3.2；**确认集只运行一次**（run_confirmation.sh 硬编码种子 + RUN_COMPLETE 标记机械强制，崩溃恢复须同种子）
- [ ] 主实验（`make confirm`）→ `make bootstrap-confirm` 判门 v2（2026-09-28 周末）
- [ ] 步骤三：规则类型消融（9 条件 × 3 ε）→ 图 3 图 4 三表 → 英文初稿 → MiTA 投稿
