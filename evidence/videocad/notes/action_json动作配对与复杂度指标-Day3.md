# VideoCAD `action_json` 动作配对与复杂度指标（Day3）

更新时间：2026-02-26

## 1. Day3 目标与产物

### 目标

1. 将 `started/finished` 事件配对，验证动作序列可用于“动作片段时长”预实验
2. 生成可复现的复杂度指标摘要（用于后续最小原型与申报证据台账）
3. 抽样探查 `qa.json` 与 `action_json` 的直接对齐可行性

### 本次新增产物

1. 脚本：`evidence/videocad/scripts/analyze_action_pairing_and_complexity.py`
2. 配对摘要（JSON）：`evidence/videocad/notes/action_json_pairing_summary.json`
3. 高复杂度样本清单（CSV）：`evidence/videocad/notes/action_json_top_complex_files.csv`
4. `qa.json` 探查摘要（JSON）：`evidence/videocad/notes/qa_json_probe_summary.json`

## 2. 动作起止配对结果（全量 `44,291` 文件）

1. 配对问题文件数：`0`
2. 严格嵌套（LIFO）不匹配文件数：`0`
3. 时间戳非单调文件数：`0`
4. 负时长配对数：`0`
5. 成功配对动作片段总数：`1,065,533`

结论：`action_json` 可稳定支持“动作起止配对 -> 时长估计 -> 复杂度指标”的最小原型。

## 3. 配对后时长统计（按动作）

总体（已配对动作）平均时长：
- `793.6766 ms`

按动作（节选）：

1. `Drawing Line`
- 配对数：`449,218`
- 平均：`296.1245 ms`
- 中位数：`186 ms`

2. `Drawing Circle`
- 配对数：`76,411`
- 平均：`345.4196 ms`
- 中位数：`242 ms`

3. `Drawing Arc`
- 配对数：`56,948`
- 平均：`555.0845 ms`
- 中位数：`302 ms`

4. `Drawing Sketch`
- 配对数：`185,632`
- 平均：`1029.1081 ms`
- 中位数：`660 ms`

5. `Drawing Curve`
- 配对数：`148,662`
- 平均：`1377.2091 ms`
- 中位数：`864 ms`

6. `Performing Extrusion`
- 配对数：`148,662`
- 平均：`1741.4356 ms`
- 中位数：`1767 ms`
- 最大值：`315,032 ms`（存在长尾）

说明：`Performing Extrusion` 时长显著高于基础绘制动作，适合后续作为复杂度/阶段切分指标之一。

## 4. 复杂度指标（文件级）可直接复用项

脚本已输出每个文件的以下指标（并按复杂度排序导出 Top CSV）：

1. `event_count`：事件总数
2. `pair_count`：成功配对动作数
3. `unique_action_count`：动作类别数
4. `span_ms`：序列总时间跨度
5. `max_nesting_depth`：最大嵌套深度
6. `pairing_completion_rate`：配对完成率

全量摘要（文件级）：

1. `pair_count`（单文件）
- 最小：`8`
- 最大：`69`
- 均值：`24.0576`
- 中位数：`21`

2. `unique_action_count`（单文件）
- 最小：`4`
- 最大：`6`
- 均值：`4.6308`

3. `max_nesting_depth`（单文件）
- 全部为 `3`

4. `pairing_completion_rate`
- 全部为 `1.0`

## 5. `qa.json` 联动探查（可行性判断）

探查摘要：`evidence/videocad/notes/qa_json_probe_summary.json`

结果：

1. `qa.json` 共 `6,000` 条问答，`id` 范围 `0..5999`
2. 模板类型均衡：6类模板各 `1,000` 条
3. 图片路径集中为：
- `ml_dataset/multi_extrude/qa/images/image_*.png`
4. QA 引用图片索引范围：
- `image_0.png` 到 `image_14653.png`

当前结论（重要）：
- 在 `qa.json` 字段中未发现可直接映射到 `action_json/XXXXXXXX.json` 的 8 位文件编号
- 若要建立稳健对齐关系，下一步需要下载并检查 `cad_imgs.zip`（以及可能的样本映射元数据/目录结构）

## 6. 对 Day4 的直接建议

1. 实现“文件级复杂度标签器”
- 例如按 `pair_count/span_ms/action_diversity` 划分低/中/高复杂度

2. 输出小规模预实验样本集（CSV/JSONL）
- 从 `action_json_top_complex_files.csv` 抽取 Top-N 与随机样本各一批

3. 下载并抽样 `cad_imgs.zip`
- 验证 `qa.json` 图片路径与动作序列文件是否存在目录级/编号级映射

