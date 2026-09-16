# 论文写作决议（随实验进展更新；2026-09-16 起）

> 本文件记录写作层面的预登记决定。分析口径的预登记见
> `audit-2026-09-15-data-lineage-and-rng.md` §3.2，两者不冲突时以审计为准。
> 里程碑 git tag 见审计 §4.6（可审计性的锚点）。

## 1. 摘要主句：不变性 + 可实现性区分（2026-09-16 二修锁定，替代首版）

**v2（现行，申请人 2026-09-16 亲定，verbatim）**：

> min_rules sustains a threshold of 0.193 invariant across all error-repeatability
> and budget settings, by construction. Realizable retry (retry_selfreport) never
> exceeds 0.033 anywhere on the grid. An oracle-detection retry — an **unattainable
> upper bound** — ranges from 0.020 to 0.250 and surpasses the rule threshold only
> when errors are transient and retry budget is ample.

**v1（2026-09-16 首版，已作废）**仅以 +0.174 的不变性表述为主句，未区分 oracle 重试与
可实现重试——retry_selfreport 全网格 ≤ 0.033（最好的格子也只有 no_rules 的 1.9×），
唯一能越过规则线 0.1934 的是依赖完美故障检测的 retry_oracle。只写 "retry ranges
0.019–0.250" 会让读者带走"重试有时更优"的错误处方。

**硬性规定**："**unattainable upper bound**" 这个限定词必须在**摘要、Results 首段、
结论**三处同时出现。+0.174（主格 Δε\*）放 Results，不放摘要首句。

## 2. 图序（2026-09-16 锁定）

- **主图 = ε\*–ρ 曲线**（`scripts/eps_star_grid_summary.py --plot` 生成）：横轴 ρ、
  纵轴 ε\*、每臂一条线、r=0.2/0.5 两个 panel。一张图同时展示效应（线间距）、
  机制（oracle 陡降）、边界条件（r=0.5 panel 在 ρ≈0 附近与 min_rules 水平线交叉）
  与不变性（min_rules 水平）。这张图回答"为什么、什么时候"。
- **森林图（bootstrap CI）降为次图**：只回答"显著吗"。
- 图 2（成功率–ε 曲线）与图 4（消融）维持方案 v1 交付物清单。

## 3. 不变性报告的构造定性（2026-09-16 二修新增，防 F5 类错误的软版本）

min_rules 与 no_rules 的极差为 0 是**定义必然**：两臂不重试，ρ 与 r 只作用于重试流。
正文与图注必须同时写死（verbatim）：

> min_rules and no_rules do not retry, hence are invariant to (ρ, r) by
> construction; the table documents this invariance rather than discovering it.
> The substantive quantity is the (ρ, r) locus at which retry_oracle crosses the
> fixed min_rules threshold.

ε\* 跨条件极差表降级为该不变性的**记录件**；实体量是交叉轨迹——事后探索已定位：
**ρ = 0 处 r\* ≈ 0.233**（r < 0.233 规则守线，r > 0.233 oracle 越线；r=0.2 → 0.178 线下，
r=0.25 → 0.201 线上）。标注为**预登记之外的事后探索**，不进任何检验族、不影响门 v2。

## 4. ρ=0 引用的硬性写法（审计 §3.4 复查项 4 的写作侧执行）

凡引用 ρ=0 的 Δε\*：必须同句给出 r 条件；r=0.5 的翻号发现进正文（承重项，
medium/high 显著为负，low 平局）；表述用"重试在预算充足时有效"，禁用"重试更强"。

## 5. 数据可用性（2026-09-16 新增，投稿前硬条件）

论文将写 "seeds are fixed and released"——补充材料 DOI 必须在 **2026-10-15 前实际
存在**并写进论文，不得留作计划。执行清单见 `docs/zenodo-submission-checklist.md`
（`make supp-bundle` 一键打包；占号与上传需申请人 Zenodo/OSF 账号操作）。
