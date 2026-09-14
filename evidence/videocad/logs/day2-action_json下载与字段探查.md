# Day2 `action_json` 下载与字段探查日志（VideoCAD）

日期：2026-02-26

## 已完成

1. 下载 `action_json.zip`（成功）
- 来源：Harvard Dataverse API `access/datafile/11828777`
- 本地文件：`evidence/videocad/samples/dataverse/action_json.zip`
- 本地 MD5：`896f6941bd734b4ee9a45f33c774f4e2`（与元数据一致）

2. 解压并完成结构确认（成功）
- 解压目录：`evidence/videocad/samples/dataverse/action_json_unpacked/action_json`
- JSON 文件数：`44,291`
- 解压体量：约 `264MB`
- 文件结构：每个文件为事件列表（JSON array）

3. 编写最小解析脚本（成功）
- 脚本路径：`evidence/videocad/scripts/inspect_action_json.py`
- 功能：
  - 全量扫描 `.json` 文件
  - 字段频次统计
  - 状态/动作分布统计
  - 单文件事件数与时长分布统计
  - 时间戳单调性检查
  - 输出摘要 JSON

4. 生成机器可读统计摘要（成功）
- 输出文件：`evidence/videocad/notes/action_json_summary.json`
- 核心结果：
  - 文件数：`44,291`
  - 事件总数：`2,131,066`
  - 字段固定为 `timestamp/status/action`
  - `status` 两类：`started/finished`（数量相等）
  - `action` 六类（含 `Drawing Line`, `Performing Extrusion` 等）

5. 形成中文字段说明与统计记录（成功）
- 文档：`evidence/videocad/notes/action_json字段与序列统计-Day2.md`

## 阻塞/异常

1. 无实质阻塞
- 备注：命令行中 `sort | head` 出现 `Broken pipe` 为正常现象（`head` 提前退出），不影响数据处理结果。

## 对 Day3 的建议起点

1. 基于 `action_json` 做“动作起止配对”最小原型
- 目标：按文件恢复动作片段时长（start-finish pairing）

2. 生成一份“复杂度指标脚本”
- 指标建议：序列长度、动作种类数、线段/圆弧/拉伸比例、总时长

3. 抽样联动 `qa.json`
- 尝试通过文件编号建立对齐关系（若存在），验证是否能形成“动作序列 -> 文本问答/任务描述”小样本

