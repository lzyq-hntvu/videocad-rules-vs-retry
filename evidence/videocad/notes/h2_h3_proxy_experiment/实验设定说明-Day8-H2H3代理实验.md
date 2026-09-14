# 实验设定说明（Day8：H2/H3 机制代理实验）

更新时间：2026-02-26

## 1. 实验目的（主线对应）

1. `H3`：验证误差注入强度 `ε` 增大时，动作链执行成功率是否出现阈值式下降，并比较不同复杂度层的阈值差异。
2. `H2`：验证加入最小规则约束后，是否能够抑制级联失败（表现为阈值抬升、失败步数延后）。

## 2. 实验对象（可复现实验样本）

1. 数据来源：`evidence/videocad/notes/cad_action_multimodal_samples.csv`
2. 样本选择：仅使用 `random_stratified_overlap` 组
3. 分层数量：
- `low` 30 条
- `medium` 30 条
- `high` 30 条
- 合计 `90` 条动作链

说明：样本已来自前序复杂度分层与图像-动作重叠样本池，属于“无 QA 映射版”可控预实验集合。

## 3. 误差注入定义（ε）

### 3.1 误差代理层级

当前为**事件级符号链代理实验**（非 GUI 元素框扰动），用于先验证链式传播与规则抑制机制。

每个事件包含：
- `status ∈ {started, finished}`
- `action ∈ {Drawing Line, Drawing Sketch, ...}`

### 3.2 注入方式

对每个事件，以概率 `ε` 进行一次扰动（per-event corruption probability）。

扰动类型：

1. `action_swap`（权重 `0.7`）
- 将动作名替换为其他动作类型（从动作词表中随机选取）

2. `status_flip`（权重 `0.3`）
- `started <-> finished` 翻转

## 4. 对照条件（H2）

### 条件 A：`no_rules`（无规则）

直接执行扰动后的事件链；若出现以下情况即判为失败：

1. `finish` 时栈下溢（无可关闭动作）
2. `finish` 动作与当前栈顶动作不一致
3. 累积错配率超过阈值（见指标定义）
4. 序列结束时栈非空

### 条件 B：`with_rules`（最小规则约束）

在执行前对事件做最小规则投影：

1. 若 `finish` 动作与栈顶不一致，投影为“关闭当前栈顶动作”
2. 若出现非法 `finish` 下溢，将该事件转换为 `started`

目的：模拟“规则约束器/动作空间限制器”对级联失败的抑制作用。

## 5. 指标定义（H3/H2 共用）

1. `success_rate`
- 在给定 `ε`、复杂度层、规则条件下，完整执行成功的比例

2. `mean_fail_step_ratio`
- 平均失败位置 / 链长度（`1.0` 表示链条完整通过）

3. `epsilon*`（阈值代理）
- 定义为成功率首次低于 `0.5` 的 `ε` 值（离散近似）

4. 辅助指标
- `mean_mismatch_rate`
- `mean_repaired_events`（仅 `with_rules`）

## 6. 参数配置（本轮）

1. `ε ∈ {0.00, 0.02, ..., 0.20}`
2. 每条链每个 `ε` 的 Monte Carlo 重复次数：`40`
3. 累积错配率阈值：`0.12`
4. 随机种子：`20260226`

## 7. 结果文件（本轮）

1. 曲线汇总：`evidence/videocad/notes/h2_h3_proxy_experiment/curve_summary.csv`
2. 单次运行明细：`evidence/videocad/notes/h2_h3_proxy_experiment/per_run_results.csv`
3. 摘要：`evidence/videocad/notes/h2_h3_proxy_experiment/summary.json`
4. 图像（机制图）：
- `evidence/videocad/notes/h2_h3_proxy_experiment/h3_h2_success_rate_vs_epsilon.png`
- `evidence/videocad/notes/h2_h3_proxy_experiment/h3_h2_fail_step_ratio_vs_epsilon.png`

## 8. 表述边界（写入申请书时需保留）

1. 当前结果为“机制代理实验”（symbolic chain proxy），用于验证误差传播与规则抑制的可观测现象。
2. 尚未使用 GUI 元素框级感知误差注入，因此不能表述为“真实视觉定位误差实验结论”。
3. 后续可在恢复 GUI 元素/感知代理后，将 `ε` 从符号链误差代理升级为图像侧感知误差代理。

