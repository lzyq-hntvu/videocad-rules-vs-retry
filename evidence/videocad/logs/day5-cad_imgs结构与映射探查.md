# Day5 `cad_imgs` 结构与映射探查日志（VideoCAD）

日期：2026-02-26

## 已完成

1. 下载 `cad_imgs.zip`（成功）
- Dataverse API `access/datafile/11828775`
- 本地文件：`evidence/videocad/samples/dataverse/cad_imgs.zip`
- 大小：约 `1GB`
- MD5 校验通过（与元数据一致）

2. 完成 `cad_imgs.zip` 目录结构探查（成功，采用兼容方案）
- `unzip` / Python `zipfile` 读取失败（central directory / `BadZipFile`）
- 使用 `bsdtar -tf` 进行目录枚举与结构分析

3. 编写映射探查脚本（成功）
- 脚本：`evidence/videocad/scripts/probe_cad_imgs_mapping.py`
- 功能：
  - 枚举 `cad_imgs.zip` 目录项
  - 校验命名模式 `images/<shard>/<sample_id>_<view>.png`
  - 比对 `action_json` 8位编号重叠
  - 检查 `qa.json` 路径是否直接命中
  - 导出重叠样本 CSV

4. 生成探查摘要与重叠样本证据（成功）
- 摘要：`evidence/videocad/notes/cad_imgs_mapping_probe_summary.json`
- CSV：`evidence/videocad/notes/cad_action_overlap_samples.csv`
- 核心结果：
  - 图像文件：`236,321`
  - 唯一样本编号：`48,918`
  - 与 `action_json` 重叠样本编号：`12,145`
  - `qa.json` 路径对 `cad_imgs.zip` 直接命中：`0`

5. 输出 Day5 中文说明文档（成功）
- `evidence/videocad/notes/cad_imgs与action_json映射探查-Day5.md`

## 阻塞/异常（已记录）

1. `cad_imgs.zip` 工具兼容性问题
- `unzip` 与 Python `zipfile` 无法读取该 ZIP 目录
- `bsdtar` 可列目录但返回退出码 `1`（stderr: `ZIP decompression failed (-5)`)
- 当前处理：将其作为兼容性风险记录；仍可基于目录枚举完成映射探查

## 对 Day6 的建议起点

1. 查 `VideoCAD` 预处理脚本（QA 图像重编号规则）
- 目标：恢复 `qa.json image_<N>.png` 到 `sample_id` 的映射

2. 先做“无 QA 映射版”图文联动样本池
- 使用 `cad_action_overlap_samples.csv` 中的 `12,145` 个重叠样本

3. 开始整理申请书可用证据叙述
- 已具备：动作配对、复杂度分层、图像-动作候选映射

