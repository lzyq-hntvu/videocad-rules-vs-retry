# VideoCAD 最小预实验任务定义（Day4）

更新时间：2026-02-26

用途：作为“无真实课程版”研究基础的可复现实验任务说明，配合 `action_json` 公开数据与本地脚本产物使用。

## 任务 A：动作时长统计与分布分析（已具备执行条件）

### 输入

1. `evidence/videocad/samples/dataverse/action_json_unpacked/action_json/*.json`
2. 配对脚本：`evidence/videocad/scripts/analyze_action_pairing_and_complexity.py`

### 输出

1. 动作级时长分布（按 `Drawing Line / Performing Extrusion` 等）
2. 文件级配对统计与异常检查结果

### 核心指标（已验证可计算）

1. 动作片段时长（ms）
2. 各动作 P50/P90/P95/P99
3. 配对完成率
4. 异常率（负时长、嵌套不匹配、时间戳非单调）

### 当前结论（Day3）

1. 配对问题文件：`0`
2. 严格嵌套不匹配：`0`
3. `Performing Extrusion` 平均时长高于基础绘制动作，适合复杂度特征建模

## 任务 B：文件级复杂度分级（已具备执行条件）

### 输入

1. `action_json` 文件集（同上）
2. 标签脚本：`evidence/videocad/scripts/label_action_complexity_and_sample.py`

### 输出

1. 全量复杂度指标表：`evidence/videocad/notes/action_json_file_complexity_metrics.csv`
2. 复杂度标签摘要：`evidence/videocad/notes/action_json_complexity_label_summary.json`
3. 分层样本清单：`evidence/videocad/notes/action_json_complexity_samples.csv`

### 指标与标签

1. 指标：`pair_count`, `span_ms`, `unique_action_count`, `extrusion_pair_count`
2. 标签：`low / medium / high`（基于复杂度分数三分位）

### 当前结论（Day4）

1. 标签分布接近均衡（约 `1/3` 每层）
2. 已形成 `150` 条可复现实验样本清单（随机分层 + 极端样本）

## 任务 C：QA 联动验证（部分具备，待补映射证据）

### 已知条件

1. `qa.json` 已下载并完成结构探查
2. `qa.json` 指向 `ml_dataset/multi_extrude/qa/images/image_*.png`

### 当前限制

1. 未发现 `qa.json` 中直接映射到 `action_json/XXXXXXXX.json` 的编号字段
2. 需要 `cad_imgs.zip`（及可能的目录/映射文件）进一步验证

### 下一步最小动作

1. 下载/抽样 `cad_imgs.zip`
2. 检查目录结构与文件命名规则
3. 判断是否能建立“动作序列 -> QA图像 -> QA模板”的稳定映射

## 申报书可用表述（草案方向，非最终正文）

1. 基于公开 VideoCAD 数据构建了可复现的 CAD UI 动作序列预实验管线
2. 完成动作起止配对、时长统计与异常校验，实现文件级复杂度分层与样本清单生成
3. 在缺少真实课程数据条件下，形成了后续原型验证所需的数据处理脚本、指标体系与证据台账

