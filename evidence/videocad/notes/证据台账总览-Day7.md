# VideoCAD 7天落地验证证据台账总览（Day7 收口）

更新时间：2026-02-26

## 1. 收口结论（Day1-Day6）

在“无真实课程/学生数据”的前提下，已基于公开 VideoCAD 数据完成一条可复现的预实验数据管线，并形成脚本、日志、统计摘要和样本清单等证据化产物。当前已具备：

1. 动作序列质量核验与字段稳定性确认
2. 动作起止配对与时长统计
3. 文件级复杂度分层与分层抽样
4. `cad_imgs` 与 `action_json` 的样本编号级候选映射验证
5. “无 QA 映射版”图像-动作联动样本池（可直接用于预实验）

## 2. 核心指标（已验证）

### 2.1 `action_json`（Day2/Day3）

1. 文件数：`44,291`
2. 事件总数：`2,131,066`
3. 动作类型数：`6`
4. `status` 分布：
- `started`: `1,065,533`
- `finished`: `1,065,533`

### 2.2 动作配对结果（Day3）

1. 成功配对动作片段：`1,065,533`
2. 配对问题文件：`0`
3. 严格嵌套不匹配文件：`0`
4. 负时长配对数：`0`

### 2.3 复杂度分层（Day4，全量 `action_json`）

1. `low`: `14,616`
2. `medium`: `15,059`
3. `high`: `14,616`

### 2.4 `cad_imgs` 映射探查（Day5）

1. CAD 图像文件数（目录枚举）：`236,321`
2. `cad_imgs` 唯一样本编号数：`48,918`
3. 与 `action_json` 重叠样本编号数：`12,145`
4. `qa.json` 路径对 `cad_imgs.zip` 直接命中：`0`

### 2.5 图像-动作联动样本池（Day6）

1. 重叠子集合并样本：`12,145`
2. 重叠子集复杂度分布：
- `low`: `4,004`
- `medium`: `4,206`
- `high`: `3,935`
3. 联动样本清单导出：`135` 条（分层随机 + 极端样本）

## 3. 当前可主张的“研究基础”边界（如实）

1. 可主张
- 已建立公开数据上的可复现预实验管线（动作序列解析、配对、复杂度分层、图像-动作候选映射）
- 已形成样本清单与脚本化处理流程，可直接用于后续原型验证

2. 不应主张
- 真实课程教学验证结果
- 学生学习效果数据
- 已完成 QA 映射恢复（当前尚未恢复 `image_<N>.png -> sample_id` 规则）

## 4. 关键证据文件（建议优先引用）

1. 数据来源与前提
- `evidence/videocad/notes/数据来源记录.md`
- `evidence/videocad/logs/day1-连通与下载验证.md`

2. 动作序列处理与统计
- `evidence/videocad/notes/action_json字段与序列统计-Day2.md`
- `evidence/videocad/notes/action_json动作配对与复杂度指标-Day3.md`
- `evidence/videocad/notes/action_json_complexity_label_summary.json`

3. 图像-动作映射与联动样本
- `evidence/videocad/notes/cad_imgs与action_json映射探查-Day5.md`
- `evidence/videocad/notes/cad_action_overlap_samples.csv`
- `evidence/videocad/notes/cad_action_multimodal_samples.csv`

4. 申请书素材
- `evidence/videocad/notes/申请书可用素材-研究基础与预实验-Day6.md`

5. 机器可读台账（Day7）
- `evidence/videocad/notes/证据台账清单-Day7.json`

## 5. Day7 后建议（若继续）

1. 文稿线：将 Day6/Day7 素材回填到申请书“研究基础”“研究方案可行性”“预实验设计”
2. 技术线：继续追踪 QA 生成脚本，恢复 `qa.json` 重编号映射规则
3. 原型线：基于 `cad_action_multimodal_samples.csv` 启动最小联动模型/规则基线

