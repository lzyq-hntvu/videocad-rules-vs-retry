# Day6 联动样本池与脚本线索日志（VideoCAD）

日期：2026-02-26

## 已完成

1. 生成“无 QA 映射版”图像-动作联动样本池（成功）
- 脚本：`evidence/videocad/scripts/build_cad_action_overlap_sample_pool.py`
- 输入：
  - `evidence/videocad/notes/cad_action_overlap_samples.csv`
  - `evidence/videocad/notes/action_json_file_complexity_metrics.csv`
- 输出：
  - `evidence/videocad/notes/cad_action_overlap_enriched.csv`
  - `evidence/videocad/notes/cad_action_multimodal_samples.csv`
  - `evidence/videocad/notes/cad_action_multimodal_sample_pool_summary.json`

2. 联动样本池结果（成功）
- 重叠子集合并样本：`12,145`
- 复杂度标签分布（重叠子集）：
  - `low`: `4,004`
  - `medium`: `4,206`
  - `high`: `3,935`
- 分层样本清单总计：`135` 条（随机分层 + 各层 top15）

3. 抓取并分析官方预处理脚本（成功）
- 源码保存：`evidence/videocad/notes/sources/generate_dataset.py`
- 关键线索：
  - 使用 `video_base`（样本编号）构造图像路径
  - 图像命名采用 `<sample_id>_0.png`
  - 路径形式与 `cad_imgs.zip` 命名规则一致

4. 输出 Day6 说明与申请书素材草案（成功）
- `evidence/videocad/notes/cad_action联动样本池与脚本线索-Day6.md`
- `evidence/videocad/notes/申请书可用素材-研究基础与预实验-Day6.md`

## 阻塞/异常

1. `qa.json` 重编号图像映射规则仍未恢复
- `generate_dataset.py` 不包含 QA 子集重编号逻辑
- 仍需后续查找 QA 生成脚本或映射工件

## 对 Day7 的建议起点（收口）

1. 汇总 Day1-Day6 证据台账（数据来源、脚本、日志、摘要）
2. 形成申请书“研究基础 + 预实验设计 + 风险与计划”结构化草稿
3. 若继续技术线：追踪 QA 生成脚本，尝试恢复 `image_<N>.png -> sample_id`

