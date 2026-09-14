# 申请书回填结构化草稿（Day7 收口版）

更新时间：2026-02-26

用途：将 Day1-Day6 的证据化产物组织为可直接改写进申请书的结构框架（不是最终正文）。

## 一、前期工作基础（公开数据与可复现处理管线）

### 可写要点

1. 已完成公开 VideoCAD 数据来源核验，并确认研究场景为 `Onshape` 浏览器 CAD 环境
2. 已建立公开数据的脚本化处理流程，覆盖动作序列解析、配对、时长统计与复杂度分层
3. 已形成图像-动作候选映射与联动样本池，为后续原型验证提供数据基础

### 可引用证据

1. `evidence/videocad/notes/数据来源记录.md`
2. `evidence/videocad/logs/day1-连通与下载验证.md`
3. `evidence/videocad/notes/证据台账总览-Day7.md`

## 二、预实验设计与已完成验证（无课程版）

### 任务 A：动作序列质量核验与时长统计（已完成）

可写要点：

1. 全量扫描 `44,291` 个动作序列文件、`2,131,066` 条事件
2. 事件字段稳定（`timestamp/status/action`）
3. 完成 `1,065,533` 个动作片段起止配对，未发现配对异常文件

可引用证据：

1. `evidence/videocad/notes/action_json字段与序列统计-Day2.md`
2. `evidence/videocad/notes/action_json动作配对与复杂度指标-Day3.md`
3. `evidence/videocad/notes/action_json_pairing_summary.json`

### 任务 B：复杂度分层与样本清单构建（已完成）

可写要点：

1. 基于动作片段数、时间跨度、动作类别数、拉伸动作数构建复杂度指标
2. 对 `44,291` 个样本完成 `low/medium/high` 分层
3. 输出分层随机样本与极端样本清单，用于后续预实验比较

可引用证据：

1. `evidence/videocad/notes/action_json复杂度标签与分层抽样-Day4.md`
2. `evidence/videocad/notes/action_json_complexity_label_summary.json`
3. `evidence/videocad/notes/action_json_complexity_samples.csv`

### 任务 C：图像-动作联动样本池（已完成第一阶段）

可写要点：

1. 从 `cad_imgs` 中识别 `48,918` 个图像样本编号
2. 与 `action_json` 建立 `12,145` 个重叠样本编号的候选映射
3. 生成“无 QA 映射版”图像-动作联动样本池，支持后续多模态原型预实验

可引用证据：

1. `evidence/videocad/notes/cad_imgs与action_json映射探查-Day5.md`
2. `evidence/videocad/notes/cad_action_overlap_samples.csv`
3. `evidence/videocad/notes/cad_action_multimodal_samples.csv`

## 三、可行性说明（方法与工程可行）

### 可写要点

1. 数据处理链路已脚本化，具备可复现实验条件
2. 关键步骤（字段解析、配对、分层、样本池构建）已有机器可读摘要与日志支撑
3. 官方预处理脚本线索支持使用 `sample_id` 连接 CAD 图像与动作样本

可引用证据：

1. `evidence/videocad/notes/sources/generate_dataset.py`
2. `evidence/videocad/notes/cad_action联动样本池与脚本线索-Day6.md`
3. `evidence/videocad/notes/证据台账清单-Day7.json`

## 四、边界与风险（需如实表述）

### 可写要点

1. 当前成果基于公开数据和自建脚本，不构成课程教学实证结果
2. `qa.json` 中 `image_<N>.png` 的重编号映射尚未恢复，暂未完成序列-图像-QA 三方稳定联动
3. 后续计划是补充 QA 生成脚本/映射工件后，再扩展到 QA 联动预实验

## 五、后续工作计划（与申请书工作包衔接）

### 可写要点

1. 完成 QA 重编号映射恢复与三方联动样本构建
2. 基于联动样本池开展最小原型验证（复杂度分级、动作统计、图像-动作关系建模）
3. 在具备真实场景条件后补充课程/实训数据验证

