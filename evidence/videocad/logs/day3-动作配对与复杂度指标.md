# Day3 动作配对与复杂度指标日志（VideoCAD）

日期：2026-02-26

## 已完成

1. 实现动作起止配对与复杂度统计脚本（成功）
- 脚本：`evidence/videocad/scripts/analyze_action_pairing_and_complexity.py`
- 功能：
  - `started/finished` 配对（按动作名栈）
  - 严格嵌套（LIFO）检查
  - 负时长/异常配对检查
  - 文件级复杂度指标统计（`pair_count`, `span_ms`, `max_nesting_depth` 等）
  - 导出 Top-N 高复杂度样本 CSV

2. 全量扫描并生成配对摘要（成功）
- 输入目录：`evidence/videocad/samples/dataverse/action_json_unpacked/action_json`
- 输出：`evidence/videocad/notes/action_json_pairing_summary.json`
- 核心结果：
  - 文件数：`44,291`
  - 配对问题文件：`0`
  - 严格嵌套不匹配文件：`0`
  - 负时长配对：`0`
  - 成功配对动作片段：`1,065,533`

3. 导出高复杂度样本清单（成功）
- 文件：`evidence/videocad/notes/action_json_top_complex_files.csv`
- 本次导出数量：`Top 120`

4. 完成 `qa.json` 联动可行性探查（抽样/结构级）
- 摘要：`evidence/videocad/notes/qa_json_probe_summary.json`
- 结论：
  - `qa.json` 使用 `ml_dataset/multi_extrude/qa/images/image_*.png` 路径
  - 当前字段中未发现 `action_json` 的 8 位文件名直接映射线索
  - 后续需要 `cad_imgs.zip` 等补充文件验证映射关系

5. 输出 Day3 中文说明文档（成功）
- `evidence/videocad/notes/action_json动作配对与复杂度指标-Day3.md`

## 阻塞/异常

1. 无实质阻塞

## 对 Day4 的建议起点

1. 做“复杂度标签器”与抽样器
- 从 `action_json_top_complex_files.csv` 生成低/中/高复杂度样本列表

2. 下载 `cad_imgs.zip` 小样本探查
- 目标：验证 QA 图像路径与动作序列是否存在稳定映射

3. 形成最小预实验任务定义（可直接写入申请书草稿）
- 任务 A：动作时长估计/统计
- 任务 B：复杂度分级
- 任务 C：序列特征与 QA 模板类型关联（待映射验证后开展）

