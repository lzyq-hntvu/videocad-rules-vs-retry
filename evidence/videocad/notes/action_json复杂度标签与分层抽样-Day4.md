# VideoCAD `action_json` 复杂度标签与分层抽样（Day4）

更新时间：2026-02-26

## 1. Day4 目标

1. 建立文件级复杂度标签（低/中/高）
2. 生成可复现的分层抽样清单，作为预实验样本池
3. 为后续“任务定义/申请书回填”提供可引用证据

## 2. 本次新增产物

1. 脚本：`evidence/videocad/scripts/label_action_complexity_and_sample.py`
2. 全量指标表（CSV）：`evidence/videocad/notes/action_json_file_complexity_metrics.csv`
3. 分层抽样清单（CSV）：`evidence/videocad/notes/action_json_complexity_samples.csv`
4. 标签摘要（JSON）：`evidence/videocad/notes/action_json_complexity_label_summary.json`

## 3. 复杂度标签方法（可复现）

### 文件级指标（从 `action_json` 提取）

1. `pair_count`：动作片段数（用 `started` 数计）
2. `span_ms`：时间跨度（`max(timestamp)-min(timestamp)`）
3. `unique_action_count`：动作类别数
4. `extrusion_pair_count`：拉伸动作片段数

### 复杂度分数（归一化加权）

`score = 0.40*norm(pair_count) + 0.35*norm(span_ms) + 0.15*norm(unique_action_count) + 0.10*norm(extrusion_pair_count)`

### 标签划分

基于 `complexity_score` 三分位（tertiles）：

1. `low`: `score <= q33`
2. `medium`: `q33 < score <= q67`
3. `high`: `score > q67`

阈值（本次全量计算）：
- `q33 = 0.099846`
- `q67 = 0.226596`

## 4. 全量结果（`44,291` 文件）

1. 标签数量
- `low`: `14,616`
- `medium`: `15,059`
- `high`: `14,616`

2. 指标分布（节选）
- `pair_count`: P33=`15`, P50=`21`, P67=`27`
- `span_ms`: P33=`7458.7`, P50=`10012`, P67=`13794`
- `unique_action_count`: P33=`4`, P50=`4`, P67=`5`
- `complexity_score`: P33=`0.0998`, P50=`0.1549`, P67=`0.2266`

3. 抽样清单产出
- 随机分层抽样：每层 `40` 条（共 `120`）
- 再附加各层 `top10_by_score`（共 `30`）
- 合计样本行数：`150`

## 5. 样本特征观察（用于预实验设计）

1. 低复杂度样本常见模式
- `pair_count` 较低（如 `8~14`）
- `unique_action_count` 常见为 `4`
- `span_ms` 较短（约几秒）

2. 高复杂度样本常见模式
- `pair_count` 接近上界（如 `65~68`）
- `unique_action_count` 常见为 `6`
- `span_ms` 可显著拉长（含长尾）

3. 价值
- 可构建“低/中/高复杂度”对比实验，不依赖真实课程数据

## 6. 与 Day3 的衔接

1. Day3 已验证动作配对完整且稳定（配对问题文件数为 `0`）
2. Day4 在此基础上完成“标签化 + 抽样化”，使数据可直接进入最小预实验流程

## 7. 待继续（Day4 后半段 / Day5）

1. 下载并抽样 `cad_imgs.zip`，验证 `qa.json` 的图像路径映射
2. 将抽样清单转为预实验运行清单（JSONL/CSV）
3. 形成“方法-指标-证据”三列表述，回填申请书研究基础章节

