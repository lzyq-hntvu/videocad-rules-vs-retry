# Day11 — 三项补充分析（0.7 判据重算 / k∈{1,3} 重跑 / 混合效应描述性）

日期：2026-09-16。申请人批准（编辑判断 2 否决 → 三项全执行），审计 §3.2⑥ 修正案为预登记依据。
铁律：docs/ 与 evidence/ 既有文件零改零删；本日只新增文件；确认集主跑（seed 20261015，run-once）未以任何种子重跑。

## 产出

1. **0.7 判据敏感性（重算，非重跑）** — `notes/sensitivity_criterion07/`
   - 96 条确认集曲线（4 臂 × 3 层 + pooled × 6 格）用引擎同一 eps_star 函数（import）在判据 0.7 重插值；全部未删失（criterion07_points.csv，120 行）。
   - Δε*^(0.7) 链级 bootstrap（B=9999，种子 20261018，CI 口径=gate v2 实现逐字段一致）：主格 ρ=0.9/r=0.2/pooled **+0.05751 [0.053827, 0.061212]**；ρ=0 全负（r=0.2 pooled −0.079977；r=0.5 pooled −0.130783）；ρ=0.5 pooled +0.039815。
   - 独立复核：20/20 曲线一致（recheck_20_curves.json）。
2. **k∈{1,3} 敏感性（重跑，新种子 20261017）** — `notes/sensitivity_k/`（18 格 × 1,248,000 runs = 22,464,000，含 k=2 同族重跑作族内参照；大表留 tmp/sensitivity_k/）
   - 判据 0.5 pooled Δε*（k=1/2/3）：ρ=0.9 +0.171/+0.169/+0.167（近不变）；ρ=0.5 +0.157/+0.131/+0.102；ρ=0、r=0.2 +0.064/+0.011/+0.004（k=3 n.s.）；ρ=0、r=0.5 +0.062/−0.061/−0.129（随 k 加深）。
   - 论文 k=2 参照数字一律取封存确认集（seed 20261015）。
   - 验证 b：k=2 路径≡引擎（CLI 透传）；dev 种子 20261019 两次直启引擎逐字节一致 + 120 随机三元组 15 字段 0 错配（validation_k2_path.json）。
3. **混合效应模型（描述性，§3.2⑥ 定位）** — `notes/mixed_model/`
   - 规格 `success ~ arm*eps*stratum + (1|chain)` 逐字（plan v1）；全主格 r=0.2/ρ=0.9（1,248,000 runs，无子集）聚合 62,400 binomial 行（似然等价）。
   - statsmodels 不可用 → Laplace GLMM（numpy/scipy 自实现；numpy 2.4.0 / scipy 1.16.3 / pandas 2.3.3）；收敛 |g|∞=1.33e-08；σ²=0.156851（SD 0.396）；armmin_rules OR=2082.98 [1824.66, 2377.87]（ref retry_oracle）；armmin_rules:eps_c OR=19.83；岭 λ=1e-4 FE 基准 24/24 符号一致（基准未达收敛阈，如实声明，仅方向对照）；armmin_rules:stratumhigh OR≈1.9e7 系拟完全分离，仅描述性。
   - 模型隐含 Δε*：low 0.290 / medium 0.231 / high 0.159 / pooled 0.232（与经验 +0.174 同向同排序）。

## 改稿

stage2_manuscript.md：标题整句替换；摘要敏感性句；§III-F 方法节；§V-H/§V-I 结果节 + Table VI（敏感性）/Table VII（混合系数）；Table 编号顺延（消融表 VI→VIII）；Table I 增 k 族行；§IX 删"k 未跑"旧句；Data Availability 增种子 20261017/20261018/20261019。验证 d：because/due to=0、verbatim 句完好、ρ=0 引用带 r 条件。详单见 handoffs/stage2_report.md 第八节。

## 种子台账（累计）

20260916 抽样 · 20261015 确认主跑（run-once 封存）· 20260915 门 bootstrap · 20261016 消融 · **20261017 k 重跑注入 · 20261018 敏感性族 bootstrap · 20261019 验证/dev**（后三个为本日新增申报，互异且不与既有种子重用）。
