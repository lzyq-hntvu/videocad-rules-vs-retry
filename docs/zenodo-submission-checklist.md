# Zenodo/OSF 补充材料提交清单（投稿前硬条件）

> 论文声明 "seeds are fixed and released"。本清单确保 DOI 在 2026-10-15 前实际存在。
> 占号与上传需要申请人自己的 Zenodo（推荐，GitHub 集成一键发版）或 OSF 账号——
> 这两步无法由 Agent 代做（无账号凭据），申请人按本清单操作即可。

## 打包（Agent 可重做）

```bash
make supp-bundle
# 产出 tmp/supplementary_bundle.zip + tmp/supplementary_manifest.json
```

包内容（small-file 全集，约数 MB）：
- 全部实验与抽样脚本（`evidence/videocad/scripts/run_four_arm_experiment.py`、
  `run_h2_h3_mechanism_proxy.py`、`scripts/{sample_confirm_set,bootstrap_eps_star,eps_star_grid_summary,analyze_fail_mix}.py`、`run_confirmation.sh`）
- 方案与预登记文档（`docs/experiment-plan-v1.md`、`docs/audit-2026-09-15-*.md`、
  `docs/paper-writing-notes.md`）
- 确认集清单与抽样记录（`confirm_set_600.csv`、`confirm_set_600_sampling_record.json`）
- 全部结论件结果表（六组 curve_summary / eps_star / fail_mix / summary + 两张 bootstrap 结果表 + eps_star_range）
- 主图与森林图（fig_eps_star_vs_rho.png、forest_r02.png）

## 不含在包内（另行处理）

- **per_run_results.csv**（六组约 600MB）：随 Zenodo 记录直接上传（Zenodo 单文件
  上限 50GB 无压力），或 gzip 后上传；DOI 落地前本地路径
  `evidence/videocad/notes/four_arm_confirm/*/per_run_results.csv`。
- 原始数据（VideoCAD 44,291 链）：第三方数据集（Harvard Dataverse），论文中引用
  原始 DOI，不重新分发。

## 四个种子（论文补充材料必须逐一列出）

| 用途 | 值 | 状态 |
|---|---|---|
| 开发集注入种子 | 20260226 | 已用（开发集全部运行） |
| 确认集抽样种子 | 20260916 | 已用（sample_confirm_set.py 默认） |
| 确认集注入种子 | 20261015 | 已用（§3.2 预登记，只运行一次） |
| bootstrap 种子 | 20260915 | 已用（bootstrap_eps_star.py 默认） |

## 申请人操作步骤（Zenodo，约 10 分钟）

1. 登录 https://zenodo.org → GitHub 连接 → 选 `lzyq-hntvu/videocad-rules-vs-retry`
   发布新 tag（tag 名建议 `v1.0-confirm-results`）→ Zenodo 自动建 DOI（可先点
   "Reserve DOI" 占号，拿到 10.5281/zenodo.xxxxxxx 后再上传文件）。
2. 上传 `supplementary_bundle.zip` 与六个 per_run 大表（可 gzip）。
3. 元数据：标题 "Supplementary materials for: Do Rules Beat Naive Retry? ..."；
   许可 CC-BY-4.0（代码 MIT 已在仓库）。
4. 把 DOI 写进论文 Data Availability 段与 `README.md` 本清单下方。

## DOI 落地位（填毕即完成）

```
DOI: ＿＿＿＿＿＿＿＿＿＿＿＿＿＿＿
记录日期: ＿＿＿＿＿＿＿＿
```
