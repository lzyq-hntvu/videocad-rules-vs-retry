# Day4 复杂度标签与分层抽样日志（VideoCAD）

日期：2026-02-26

## 已完成

1. 实现复杂度标签与抽样脚本（成功）
- 脚本：`evidence/videocad/scripts/label_action_complexity_and_sample.py`
- 功能：
  - 提取文件级指标（`pair_count`, `span_ms`, `unique_action_count`, `extrusion_pair_count`）
  - 计算复杂度分数（归一化加权）
  - 按三分位划分 `low/medium/high`
  - 导出全量指标表与分层抽样清单

2. 全量生成复杂度标签（成功）
- 输出：`evidence/videocad/notes/action_json_file_complexity_metrics.csv`
- 输出：`evidence/videocad/notes/action_json_complexity_label_summary.json`
- 核心结果：
  - 文件数：`44,291`
  - `low`: `14,616`
  - `medium`: `15,059`
  - `high`: `14,616`

3. 生成分层抽样样本清单（成功）
- 输出：`evidence/videocad/notes/action_json_complexity_samples.csv`
- 本次配置：
  - 随机分层每层 `40` 条（共 `120`）
  - 附加各层 `top10_by_score`（共 `30`）
  - 总计 `150` 行

4. 输出 Day4 说明与预实验任务定义（成功）
- `evidence/videocad/notes/action_json复杂度标签与分层抽样-Day4.md`
- `evidence/videocad/notes/最小预实验任务定义-Day4.md`

## 阻塞/异常

1. 无实质阻塞

## 尚未执行（待 Day4 后半段 / Day5）

1. `cad_imgs.zip` 下载与抽样探查（约 1GB）
- 用于验证 `qa.json` 图像路径与 `action_json` 的映射关系

## 对 Day5 的建议起点

1. 下载 `cad_imgs.zip` 并只做结构/命名探查（先不做全量处理）
2. 若映射成立，构建“小样本联动清单”（动作序列 + QA 图像 + 模板）
3. 将任务 A/B/C 整理为申请书“研究基础/预实验设计”段落素材

