# Day9 H1 受控域扰动代理实验日志（VideoCAD 主线回归）

日期：2026-02-26

## 已完成

1. 实现 H1 小样本受控域扰动代理实验脚本（成功）
- 脚本：`evidence/videocad/scripts/run_h1_domain_shift_proxy.py`
- 功能：
  - 从 `cad_action_overlap_enriched.csv` 按复杂度分层抽样图像
  - 从 `cad_imgs.zip` 批量抽图并缓存
  - 施加受控域扰动（亮度/对比度/模糊/尺度/遮挡/噪声）
  - 对比 `baseline` 与 `robust` 表征的图像匹配稳定性
  - 输出退化曲线与退化斜率

2. 完成一轮 H1 代理实验（成功，快速版）
- 分层抽样：`low/medium/high` 各 `100`（共 `300` 图像）
- 扰动强度：`0~4`
- 每强度重复：`2` 次（快速验证版）

3. 生成 H1 机制图与数据表（成功）
- `evidence/videocad/notes/h1_proxy_experiment/summary_curve.csv`
- `evidence/videocad/notes/h1_proxy_experiment/degradation_slopes.csv`
- `evidence/videocad/notes/h1_proxy_experiment/per_query_results.csv`
- `evidence/videocad/notes/h1_proxy_experiment/summary.json`
- `evidence/videocad/notes/h1_proxy_experiment/h1_proxy_top1_acc_vs_shift.png`
- `evidence/videocad/notes/h1_proxy_experiment/h1_proxy_mrr_vs_shift.png`
- `evidence/videocad/notes/h1_proxy_experiment/h1_proxy_top1_by_complexity.png`

4. 输出 H1 设定说明与结果解读（成功）
- `evidence/videocad/notes/h1_proxy_experiment/实验设定说明-Day9-H1代理实验.md`
- `evidence/videocad/notes/h1_proxy_experiment/结果解读-Day9-H1代理实验.md`

## 本轮关键信号（预实验观察）

1. 总体样本（`all`）上，`robust` 相比 `baseline` 退化斜率更缓（`top1_acc` 与 `MRR`）
2. `medium`、`high` 子集上信号更明显
3. `low` 子集上 `robust` 不占优，提示表征设计仍需优化

## 边界说明

1. 当前为图像匹配/检索代理实验，不是 GUI 元素定位实验
2. 可作为 H1 的机制证据入口（退化斜率与复杂度相关性），但需后续继续强化

## 下一步建议（主线整合）

1. 将 Day8（H2/H3）+ Day9（H1）三张机制图整理到同一页“预实验结果概览”
2. 在 `1.3 科学问题与研究假设` 中加入“可反驳路径与预实验观察”一段
3. 在 `5.研究基础` 中把 H1/H2/H3 的预实验观察与证据文件路径一一对应

