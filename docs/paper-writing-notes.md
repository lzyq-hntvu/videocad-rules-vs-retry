# 论文写作决议（随实验进展更新；2026-09-16 起）

> 本文件记录写作层面的预登记决定。分析口径的预登记见
> `audit-2026-09-15-data-lineage-and-rng.md` §3.2，两者不冲突时以审计为准。

## 1. 摘要主句：不变性表述，不以 +0.174 开头（2026-09-16 锁定）

+0.174 会被误读为"规则比重试强 17 个百分点"——实际上该条件下重试已近惰性
（对照量 Δε*(oracle−no_rules) ≈ 0.002，见审计 §3.2④），主格差距的 98.8% 来自
"vs 无干预"。摘要主句用不变性表述（申请人 2026-09-16 亲定，verbatim）：

> min_rules sustains a threshold of 0.193 invariant across all error-repeatability
> and budget settings, while retry_oracle ranges from 0.019 to 0.250 over the same
> grid. Rules do not buy a higher ceiling—they buy a floor that does not depend on
> how repeatable the error is or how much retry budget is available.

**+0.174（主格 Δε\*）照报，但放在 Results，不放摘要首句。**

## 2. 图序（2026-09-16 锁定）

- **主图 = ε*–ρ 曲线**（`scripts/eps_star_grid_summary.py --plot` 生成）：横轴 ρ、
  纵轴 ε*、每臂一条线、r=0.2/0.5 两个 panel。一张图同时展示效应（线间距）、
  机制（oracle 陡降）、边界条件（r=0.5 panel 在 ρ≈0 附近与 min_rules 水平线交叉）
  与不变性（min_rules 水平）。这张图回答"为什么、什么时候"。
- **森林图（bootstrap CI）降为次图**：只回答"显著吗"。
- 图 2（成功率–ε 曲线）与图 4（消融）维持方案 v1 交付物清单。

## 3. 正式报告量：各臂 ε* 跨条件极差（2026-09-16 预登记）

不变性主张的直接度量：每臂 ε* 在 (ρ, r) 网格（6 格，pooled）上的
min / max / range / max-min 倍数，输出 `eps_star_range.csv`。
min_rules 与 no_rules 预期极差为 0；retry_oracle 预期跨约一个数量级。

## 4. ρ=0 引用的硬性写法（审计 §3.4 复查项 4 的写作侧执行）

凡引用 ρ=0 的 Δε\*：必须同句给出 r 条件；r=0.5 的翻号发现进正文（承重项）；
表述用"重试在预算充足时有效"，禁用"重试更强"。
