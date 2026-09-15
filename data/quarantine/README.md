# 隔离区 — 不得引用

## preliminary_results.json.withdrawn（2026-09-15 隔离）

**状态：撤回（withdrawn）。不得用于任何图、表、论文或本子回填。**

证据见 `docs/audit-2026-09-15-data-lineage-and-rng.md`。要点：

1. 该文件不是管线输出：脚本在 ε=0 时成功率必为 1.0（零注入），文件却报 0.95/0.88/0.79——物理上不可能由本管线在任何参数下产生。
2. 声明判据 0.7，脚本真实判据 0.5；ε 网格 5 点 vs 脚本 11 档。
3. 六个 ε\* 全部精确命中 success_rate 恰好 0.70 的格点——是照阈值反推的曲线，不是测量。
4. H1 段 low/high 很可能标反（对照本子 p.16）。

文件保留在此仅供审计溯源。真实管线输出见 `evidence/videocad/notes/h2_h3_proxy_experiment/`
（已验证：同参数重跑逐字节一致）。
