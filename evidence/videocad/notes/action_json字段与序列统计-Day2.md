# VideoCAD `action_json` 字段与序列统计（Day2）

更新时间：2026-02-26

## 1. 本次处理对象

1. 数据文件：`evidence/videocad/samples/dataverse/action_json.zip`
- Dataverse `datafile id`: `11828777`
- 文件大小：约 `23MB`
- MD5（本地校验）：`896f6941bd734b4ee9a45f33c774f4e2`（与元数据一致）

2. 解压目录：`evidence/videocad/samples/dataverse/action_json_unpacked/action_json`
- 解压后体量：约 `264MB`

3. 统计脚本：`evidence/videocad/scripts/inspect_action_json.py`
4. 统计结果（JSON）：`evidence/videocad/notes/action_json_summary.json`

## 2. 结构结论（字段摘要）

1. 每个文件是一个 JSON 数组（事件序列）
2. 每个事件为对象，当前样本统计中事件字段固定为 3 个：
- `timestamp`
- `status`
- `action`

3. 字段覆盖统计（全量扫描）
- `timestamp`: `2,131,066` 次
- `status`: `2,131,066` 次
- `action`: `2,131,066` 次

结论：在本次全量扫描范围内，未发现缺失字段事件（可作为后续解析脚本的稳定输入假设）。

## 3. 规模与序列统计（全量）

1. 文件数（动作序列数）：`44,291`
2. 事件总数：`2,131,066`
3. 空文件数：`0`
4. 时间戳单调性违规文件数：`0`（按文件内事件顺序检查）

5. 单文件事件数分布（`event_count`）
- 最小值：`16`
- 最大值：`138`
- 均值：`48.1151`
- 中位数：`42`
- P90：`88`
- P95：`102`
- P99：`124`

6. 单文件持续时长分布（`max(timestamp)-min(timestamp)`，单位 ms）
- 最小值：`2414`
- 最大值：`320024`
- 均值：`12956.1641`
- 中位数：`10012`
- P90：`24943`
- P95：`30465.5`
- P99：`43208.5`

## 4. 取值分布（状态与动作）

1. `status` 取值（2类）
- `started`: `1,065,533`
- `finished`: `1,065,533`

2. `action` 取值（6类）
- `Drawing Line`: `898,436`
- `Drawing Sketch`: `371,264`
- `Drawing Curve`: `297,324`
- `Performing Extrusion`: `297,324`
- `Drawing Circle`: `152,822`
- `Drawing Arc`: `113,896`

观察：`started` / `finished` 总量完全相等，说明该文件集适合后续做“动作起止配对”或时长估计的预实验。

## 5. 样例结构（抽样）

样例文件：`00000070.json`

首事件示例：
- `{"timestamp": 1217.0, "status": "started", "action": "Drawing Curve"}`

末事件示例：
- `{"timestamp": 25366.0, "status": "finished", "action": "Performing Extrusion"}`

## 6. 对 Day3/后续的直接价值

1. 可构建“动作级序列任务”最小原型（无需真实课程数据）
- 输入：事件序列（`action/status/timestamp`）
- 输出：动作统计、阶段切分、复杂度指标

2. 可定义一组可复现实验指标
- 序列长度
- 动作类别多样性
- 起止配对完整率
- 时间跨度/节奏特征

3. 后续可扩展对接
- `mouse_json.zip`：补充光标/轨迹层面信号
- `qa.json`：构建问答或任务说明对齐实验

