# VideoCAD `cad_action` 联动样本池与脚本线索（Day6）

更新时间：2026-02-26

## 1. Day6 目标

1. 基于 `cad_imgs` 与 `action_json` 的重叠样本编号，生成“无 QA 映射版”图像-动作联动样本池
2. 补查官方预处理脚本，确认图像-动作按 `sample_id` 连接的证据

## 2. 本次新增产物

1. 联动样本池脚本：`evidence/videocad/scripts/build_cad_action_overlap_sample_pool.py`
2. 重叠样本增强表（CSV）：`evidence/videocad/notes/cad_action_overlap_enriched.csv`
3. 联动样本清单（CSV）：`evidence/videocad/notes/cad_action_multimodal_samples.csv`
4. 联动样本池摘要（JSON）：`evidence/videocad/notes/cad_action_multimodal_sample_pool_summary.json`
5. 官方预处理脚本源码（保存）：`evidence/videocad/notes/sources/generate_dataset.py`

## 3. 联动样本池（无 QA 映射版）结果

### 3.1 合并规则

按 `sample_id` 合并：

1. `cad_action_overlap_samples.csv`（来自 Day5 的 `cad_imgs`↔`action_json` 重叠样本）
2. `action_json_file_complexity_metrics.csv`（来自 Day4 的复杂度标签结果）

### 3.2 合并结果（全量重叠子集）

1. 成功合并样本数：`12,145`
2. 复杂度标签分布（重叠子集）：
- `low`: `4,004`
- `medium`: `4,206`
- `high`: `3,935`

3. `cad_imgs` 图像数量分布（重叠子集）
- `5` 张图像：`11,150` 样本（主流）
- `1~4` 张图像：少量长尾（合计 `995`）

说明：大多数重叠样本具备完整 5 视角图像（`_0.._4`），适合构建图像-动作联动预实验。

### 3.3 联动样本清单产出

`evidence/videocad/notes/cad_action_multimodal_samples.csv`

包含：

1. 随机分层样本：每层 `30` 条（共 `90`）
2. 各层高分/极端样本：每层 `top15`（共 `45`）
3. 总计：`135` 条

字段示例（节选）：
- `sample_id`
- `action_json_path`
- `example_image_paths`
- `example_view_indices`
- `pair_count`
- `span_ms`
- `complexity_score`
- `complexity_label`

## 4. 官方脚本线索（关键证据）

从 `evidence/videocad/notes/sources/generate_dataset.py` 可确认：

1. 预处理时按 `video_base`（即样本编号）匹配图像和动作/视频
2. 图像路径构造方式：
- `image_file = f\"{video_base}_0.png\"`
- `image_path = os.path.join(image_dir, video_base[:4], image_file)`

这与 Day5 发现的 `cad_imgs.zip` 命名模式一致（`images/<shard>/<sample_id>_<view>.png`），进一步支持：

`sample_id` 是连接动作序列与 CAD 图像的稳定主键（至少对训练预处理链路成立）。

## 5. 对 `qa.json` 映射问题的更新判断

1. `qa.json` 的 `image_<N>.png` 重编号规则在 `generate_dataset.py` 中未体现
2. `generate_dataset.py` 更偏向“视频/鼠标/目标 CAD 图像”训练预处理，而非 QA 子集构建

结论：
- `qa.json` 映射仍需查找其他脚本/目录工件（可能是 QA 数据生成脚本）
- 但“无 QA 映射版”联动预实验已经可以启动（基于 `12,145` 重叠样本）

## 6. 对 Day7 的建议（收口方向）

1. 输出一份申请书可用的“研究基础证据台账摘要”
2. 将 Day1-Day6 产物整理成：
- 数据来源与合规说明
- 可复现实验管线说明
- 已完成预实验动作与结果摘要
- 风险与后续补充计划（QA 映射）

