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

## 预先登记的决策门（第 2 周末执行，拿到结果后不得修改）

```
若 Δε*( min_rules − retry_oracle ) 的 95% CI 跨 0
→ 规则没有可证实的增量
→ 停止投稿
```

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

# 开发集全量复现（90 链 × 40 重复 × 11 ε 档，两臂）：
python3 evidence/videocad/scripts/run_h2_h3_mechanism_proxy.py

# 作图（需 matplotlib + numpy）：
python3 scripts/plot_h2h3_results.py
```

环境：Python 3.12（WSL2 系统 Python 即可，numpy / PIL / matplotlib 已装）。
核心模拟脚本只依赖标准库，matplotlib 缺失时自动跳过作图不报错。

## 五臂定义（方案 v1 表 A，步骤一待实现）

| 标识 | 定义 | 角色 |
|---|---|---|
| `no_rules` | 无约束，误差注入后直接执行 | 下界（✅ 已有） |
| `retry_selfreport` | 环境判非法才重试该步，每步至多 k 次 | 现实重试基线（待实现） |
| **`retry_oracle`** | 偏离预期状态转移即重试（完美检测），每步至多 k 次 | **主对照**（待实现） |
| `min_rules` | 栈一致性收束 + 非法关闭修正（= 脚本现有 `use_rules=True`） | 待检验项（✅ 已有） |
| `rules_retry` | `min_rules` + `retry_selfreport` | 互补还是冗余（待实现） |

**主断言必须对 `retry_oracle` 成立。** 只赢过 `retry_selfreport` 就如实写成较弱结论。

## 既有实验输出（从旧仓库复制，口径见各文件）

- `evidence/videocad/notes/h2_h3_proxy_experiment/` — 90 链 × 40 重复 × 11 ε，no_rules vs with_rules 两臂结果与图
- `evidence/videocad/notes/h1_proxy_experiment/` — H1 域移位代理结果
- `data/preliminary_results.json` — 本子预实验数值（H1 退化斜率等）

> 注意：既有输出的 ε\* 取格点值、判据线与正文口径不一致——方案 v1 步骤四（插值 + 链级 bootstrap CI）正是为此，新实验一律用新口径。

## 状态

- [x] 项目搭建、实验内容复制、管线冒烟（2026-09-15）
- [x] 实测单次耗时：≈0.1 ms/run（3,300 runs 计时通过 1.6s，含约 1.3s 固定启动）→
      全量 1,104,000 runs 纯模拟约 2–3 分钟，加 I/O 也在小时级以内。
      **不需要回调重复数或链数**（方案表 D 的预案不触发）
- [ ] 步骤一：三个新臂实现与单测（`retry_selfreport` / `retry_oracle` / `rules_retry`）
- [ ] 步骤二：确认集 600 条抽样（200/200/200，与开发集不相交，种子入补充材料）
- [ ] 步骤四：ε\* 插值 + 链级 bootstrap 口径锁定（先于全量开跑）
- [ ] 主实验 780,000 runs → 决策门（2026-09-28 周末）
- [ ] 步骤三：规则类型消融（9 条件 × 3 ε）→ 图 3 图 4 三表 → 英文初稿 → MiTA 投稿
