# VideoCAD `cad_imgs` 与 `action_json` 映射探查（Day5）

更新时间：2026-02-26

## 1. Day5 目标

1. 下载 `cad_imgs.zip` 并确认目录/命名结构
2. 验证是否存在 `cad_imgs` 与 `action_json` 的可行映射线索
3. 判断 `qa.json` 是否能直接用 `cad_imgs.zip` 路径解析

## 2. 本次新增产物

1. 原始文件：`evidence/videocad/samples/dataverse/cad_imgs.zip`
2. 探查脚本：`evidence/videocad/scripts/probe_cad_imgs_mapping.py`
3. 探查摘要：`evidence/videocad/notes/cad_imgs_mapping_probe_summary.json`
4. 重叠样本清单（CSV）：`evidence/videocad/notes/cad_action_overlap_samples.csv`

## 3. 下载与校验

1. Dataverse `datafile id`: `11828775`
2. 文件大小：`1,013,972,992 bytes`（约 `1GB`）
3. MD5 校验：
- 本地：`9a0cb4d8bf596df7b3c6e13d32c3d85c`
- 与元数据一致（校验通过）

## 4. 压缩包结构探查结论（不解压全量内容）

### 4.1 工具兼容性情况（重要）

1. 系统 `unzip` 与 Python `zipfile` 无法读取该文件目录（报 `BadZipFile`/central directory 相关错误）
2. `bsdtar -tf` 可枚举目录，但返回退出码 `1`，stderr 含：
- `ZIP decompression failed (-5)`

处理策略：
- 使用 `bsdtar` 列目录进行结构与命名探查（不依赖全量解压）
- 将该异常作为数据处理兼容性风险记录在案

### 4.2 命名与目录模式（已验证）

`cad_imgs.zip` 文件命名模式一致：

`images/<4-digit-shard>/<8-digit-sample-id>_<view-index>.png`

示例：
- `images/0000/00000070_4.png`
- `images/0000/00000123_3.png`
- `images/0027/...`

### 4.3 目录级统计（本次列目录结果）

1. 图像文件数：`236,321`
2. 目录数：`32`
3. 分片目录数（`shard`）：`31`
4. 视角索引分布（近似均衡）：
- `_0`: `47,259`
- `_1`: `47,289`
- `_2`: `47,245`
- `_3`: `47,230`
- `_4`: `47,298`

5. 唯一样本编号数（8位 `sample_id`）：`48,918`
6. 每个样本图像数范围（本次结果）：`1 ~ 5`

## 5. 与 `action_json` 的映射可行性（核心结论）

### 5.1 已验证的强线索

1. `cad_imgs` 图像名中包含 8 位 `sample_id`
2. `action_json` 文件名本身就是 8 位编号（如 `00000070.json`）
3. 两者存在明确重叠

### 5.2 重叠统计（本次探查）

1. `action_json` 文件数：`44,291`
2. `cad_imgs` 唯一样本编号数：`48,918`
3. 重叠样本编号数：`12,145`

覆盖率（按本次列目录结果计算）：
- `cad_imgs -> action_json` 覆盖率：`0.248273`
- `action_json -> cad_imgs` 覆盖率：`0.274209`

### 5.3 证据文件（可直接引用）

`evidence/videocad/notes/cad_action_overlap_samples.csv`

该文件包含字段：
- `sample_id`
- `image_count_in_cad`
- `action_json_exists`
- `example_image_paths`

示例（真实重叠样本）：
- `00000070` 对应 `images/0000/00000070_0.png ... _4.png`
- `00000123` 对应 `images/0000/00000123_0.png ... _4.png`

结论：已建立“动作序列文件编号 ↔ CAD 图像样本编号”的候选映射链路（至少对 `12,145` 个样本成立）。

## 6. `qa.json` 联动判断（当前状态）

1. `qa.json` 路径格式为：
- `ml_dataset/multi_extrude/qa/images/image_<N>.png`

2. 本次对 `cad_imgs.zip` 的直接路径命中结果：
- `qa_exact_path_hits_in_cad_zip = 0`

当前判断：
- `qa.json` 使用的是“重编号/重组织”的 QA 图像子集
- 仍需要额外映射工件（例如索引表、生成脚本或目录元数据）才能稳定链接到 `cad_imgs`/`action_json`

## 7. 对 Day6 的直接建议

1. 优先查找 `VideoCAD` 仓库中的 QA 生成/预处理脚本（如 `generate_dataset.py` 相关逻辑）
- 目标：定位 `image_<N>.png` 到 `sample_id` 的生成规则

2. 在现有证据基础上先做“无 QA 映射版”图文联动预实验
- 仅使用 `cad_imgs` 与 `action_json` 的 `sample_id` 重叠样本（`12,145` 个）

3. 输出一份申请书可用段落素材
- 强调“已验证公开数据中的跨模态候选映射可建立，QA 子集映射待补充脚本证据”

