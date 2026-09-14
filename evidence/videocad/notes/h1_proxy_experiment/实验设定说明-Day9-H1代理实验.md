# 实验设定说明（Day9：H1 受控域扰动鲁棒性代理实验）

更新时间：2026-02-26

## 1. 实验目的（对应 H1）

在不训练大模型的前提下，构建一个小样本、可控、可复现的视觉鲁棒性代理实验，验证：在受控域扰动（controlled domain shift）增强时，较鲁棒的表征/匹配策略是否具有更缓的性能退化斜率。

说明：本实验是“图像匹配/检索代理任务”，不是 GUI 元素定位或检测基准。

## 2. 样本来源与抽样

1. 来源：`evidence/videocad/notes/cad_action_overlap_enriched.csv`
2. 样本池基础：`cad_imgs` 与 `action_json` 已验证重叠样本（Day5/Day6）
3. 分层抽样（按复杂度标签）：
- `low` 100
- `medium` 100
- `high` 100
- 合计 `300` 张 CAD 图像（优先使用 `_0` 视角）

## 3. 图像读取与缓存

1. 数据文件：`evidence/videocad/samples/dataverse/cad_imgs.zip`
2. 读取方式：`bsdtar` 批量抽取到缓存目录（兼容 `cad_imgs.zip` 特殊 ZIP 格式）
3. 缓存目录：`evidence/videocad/notes/h1_proxy_experiment/cache_images`

备注：`bsdtar` 对该 ZIP 返回码可能为 `1`（已知兼容性警告），但图像可成功抽取并解码。

## 4. 代理任务定义（retrieval/matching proxy）

对每张原始 CAD 图像施加受控域扰动，得到查询图 `q`；在 `300` 张原始图像组成的 gallery 中检索其对应原图，比较两种表征的识别稳定性。

正确匹配定义：
- 检索结果 top-1 为该查询图的原图（同一图像样本）

## 5. 受控域扰动（controlled domain shift）

强度 `s ∈ {0,1,2,3,4}`，强度越高扰动越强。扰动为组合式（composite）：

1. 亮度/对比度抖动
2. 高斯模糊（中高强度）
3. 尺度抖动 + 回填（模拟分辨率/布局变化）
4. 局部遮挡块（高强度）
5. 高斯噪声

## 6. 对比方法（H1）

### 6.1 `baseline`（脆弱匹配代理）

1. 原始灰度图
2. `64x64` 缩放
3. 直接展平并 L2 归一化

特点：主要依赖原始外观，抗域扰动能力有限。

### 6.2 `robust`（鲁棒表征代理）

1. 灰度化 + 自动对比度 + 直方图均衡
2. 细粒度归一化外观分支（`48x48`）
3. 粗粒度强度池化分支（`12x12`）
4. 梯度幅值池化分支（`12x12`）
5. 全局直方图分支

特点：通过光照归一化、多尺度外观与梯度信息提升跨扰动稳定性。

## 7. 评价指标

1. `top1_acc`：top-1 检索准确率
2. `MRR`：mean reciprocal rank
3. 退化斜率（核心）
- 指标随扰动强度 `s` 的线性拟合斜率（越接近 0 表示退化越缓）

## 8. 本轮参数配置

1. 每个强度每张图重复次数：`2`（快速验证版）
2. 强度范围：`0~4`
3. 随机种子：`20260226`

## 9. 输出文件

1. 样本清单：`evidence/videocad/notes/h1_proxy_experiment/selected_images.csv`
2. 曲线汇总：`evidence/videocad/notes/h1_proxy_experiment/summary_curve.csv`
3. 退化斜率：`evidence/videocad/notes/h1_proxy_experiment/degradation_slopes.csv`
4. 单次检索明细：`evidence/videocad/notes/h1_proxy_experiment/per_query_results.csv`
5. 摘要：`evidence/videocad/notes/h1_proxy_experiment/summary.json`
6. 图像：
- `evidence/videocad/notes/h1_proxy_experiment/h1_proxy_top1_acc_vs_shift.png`
- `evidence/videocad/notes/h1_proxy_experiment/h1_proxy_mrr_vs_shift.png`
- `evidence/videocad/notes/h1_proxy_experiment/h1_proxy_top1_by_complexity.png`

