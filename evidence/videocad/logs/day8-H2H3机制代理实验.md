# Day8 H2/H3 机制代理实验日志（VideoCAD 主线回归）

日期：2026-02-26

## 已完成

1. 实现 H2/H3 最小机制代理实验脚本（成功）
- 脚本：`evidence/videocad/scripts/run_h2_h3_mechanism_proxy.py`
- 核心思路：
  - 在事件级符号动作链上注入误差（`ε`）
  - 对比 `no_rules` 与 `with_rules` 两种执行条件
  - 观察成功率与失败位置随 `ε` 的变化

2. 完成一轮实验运行（成功）
- 样本：`low/medium/high` 各 `30` 条（共 `90` 条）
- `ε` 范围：`0.00 ~ 0.20`（步长 `0.02`）
- Monte Carlo：每链每 `ε` 重复 `40` 次

3. 生成机制图与数据表（成功）
- `evidence/videocad/notes/h2_h3_proxy_experiment/curve_summary.csv`
- `evidence/videocad/notes/h2_h3_proxy_experiment/per_run_results.csv`
- `evidence/videocad/notes/h2_h3_proxy_experiment/summary.json`
- `evidence/videocad/notes/h2_h3_proxy_experiment/h3_h2_success_rate_vs_epsilon.png`
- `evidence/videocad/notes/h2_h3_proxy_experiment/h3_h2_fail_step_ratio_vs_epsilon.png`

4. 输出“1页实验设定说明”与结果解读（成功）
- `evidence/videocad/notes/h2_h3_proxy_experiment/实验设定说明-Day8-H2H3代理实验.md`
- `evidence/videocad/notes/h2_h3_proxy_experiment/结果解读-Day8-H2H3代理实验.md`

## 本轮关键信号（预实验观察）

1. `H3` 方向信号成立
- 复杂度越高，成功率曲线越早跌破 `0.5`（阈值更低）

2. `H2` 方向信号成立
- 加入最小规则约束后，各复杂度层阈值整体抬升，失败位置延后

## 边界说明（已明确）

1. 当前为事件级符号链代理实验（非 GUI 元素框级误差注入）
2. 可作为 H2/H3 的机制预实验入口，但不能替代真实视觉感知误差实验

## 下一步建议（Day9）

1. 开始 H1 小样本受控域扰动鲁棒性代理实验（300 张左右）
2. 形成第三张机制图（退化斜率对比）
3. 将 Day8 图和 Day7 台账一起回填到申请书 `1.3` 与 `5.研究基础` 相关段落

