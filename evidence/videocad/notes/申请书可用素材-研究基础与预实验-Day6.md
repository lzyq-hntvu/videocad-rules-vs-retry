# 申请书可用素材（研究基础与预实验）- Day6 草案

更新时间：2026-02-26

说明：以下为“无真实课程版”证据化表述素材，基于公开 VideoCAD 数据与本地脚本/日志产物形成；避免虚构教学场景、学生数据与课程验证结果。

## 1. 研究基础（公开数据 + 自建管线）

项目组围绕复杂 GUI（浏览器 CAD）交互建模需求，基于公开 VideoCAD 数据集开展了可复现的数据处理与预实验准备工作。已完成公开数据来源核验、样本下载、字段探查、动作序列配对与复杂度分层等工作，并形成可追溯脚本、日志与统计摘要，为后续方法原型验证提供了稳定的数据基础与指标框架。

## 2. 已完成的可复现实验性工作（证据化）

1. 动作序列结构与质量核验（`action_json`）
- 全量扫描 `44,291` 个动作序列文件，共 `2,131,066` 条事件
- 事件字段稳定为 `timestamp/status/action`
- 时间戳单调性检查未发现异常

2. 动作起止配对与时长统计
- 成功配对动作片段 `1,065,533` 个
- 配对异常文件数为 `0`
- 已得到按动作类型的时长分布统计（如 `Drawing Line`、`Performing Extrusion`）

3. 文件级复杂度分层与样本清单构建
- 基于 `pair_count/span_ms/unique_action_count/extrusion_pair_count` 构建复杂度分数
- 对 `44,291` 个样本完成 `low/medium/high` 分层
- 生成随机分层样本与极端样本清单，可直接用于后续预实验

4. 图像-动作候选映射验证（`cad_imgs` ↔ `action_json`）
- 从 `cad_imgs.zip` 中识别出 `48,918` 个图像样本编号
- 与 `action_json` 重叠样本编号 `12,145` 个
- 已生成重叠样本证据表与联动样本池（含复杂度标签）

## 3. 预实验任务设计（已具备执行条件）

1. 任务 A：动作时长统计与复杂度特征分析
- 输入：`action_json`
- 输出：动作时长分布、文件级复杂度指标、分层结果

2. 任务 B：图像-动作联动样本预实验（无 QA 映射版）
- 输入：`cad_imgs` 与 `action_json` 的重叠样本（`12,145`）
- 输出：分层联动样本清单（图像路径 + 动作序列路径 + 复杂度标签）

## 4. 当前边界与后续计划（如实表述）

1. `qa.json` 使用重编号 QA 图像路径（`image_<N>.png`），当前尚未恢复其到 `sample_id` 的稳定映射规则
2. 后续将继续追踪 QA 数据生成脚本/映射工件，并在此基础上扩展序列-图像-QA 三方联动验证
3. 现阶段成果定位为“公开数据上的可复现预实验管线与指标体系”，不等同于课程教学实证结果

## 5. 可引用证据文件（示例）

1. `evidence/videocad/logs/day1-连通与下载验证.md`
2. `evidence/videocad/logs/day2-action_json下载与字段探查.md`
3. `evidence/videocad/logs/day3-动作配对与复杂度指标.md`
4. `evidence/videocad/logs/day4-复杂度标签与分层抽样.md`
5. `evidence/videocad/logs/day5-cad_imgs结构与映射探查.md`
6. `evidence/videocad/notes/action_json动作配对与复杂度指标-Day3.md`
7. `evidence/videocad/notes/action_json复杂度标签与分层抽样-Day4.md`
8. `evidence/videocad/notes/cad_imgs与action_json映射探查-Day5.md`
9. `evidence/videocad/notes/cad_action联动样本池与脚本线索-Day6.md`

