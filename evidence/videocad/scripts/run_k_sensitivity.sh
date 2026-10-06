#!/bin/bash
# k ∈ {1,3} 敏感性族重跑 —— 2026-09-16 申请人批准的三项补充分析之二（审计 §3.2⑥）。
#
# ⚠ 种子申报（run-once 纪律）：
#   本运行是**敏感性族新实验**，不是确认集主跑。注入种子 20261017 与确认集主跑种子
#   20261015、消融种子 20261016 均不同；本族结果不进入、不影响门 v2 判定（审计 §3.2①）。
#   确认集主跑（seed 20261015）已封存，本脚本不触碰任何 four_arm_confirm/ 既有文件。
#
# 规格：confirm_set_600 --use-all-rows，replicates 20，budget-ratio r ∈ {0.2, 0.5}，
#       swap-prob 0.7，26 点 ε 网格 0→0.50（引擎默认），ρ ∈ {0, 0.5, 0.9}，k ∈ {1,3}。
# 输出：tmp/sensitivity_k/k{K}_r{R}_rho{RHO}/（per_run 大表留 tmp，摘要件复制入
#       evidence/videocad/notes/sensitivity_k/ 由后续脚本完成）。
set -u
cd "$(dirname "$0")/../../.."   # repo root
ENGINE=evidence/videocad/scripts/run_four_arm_experiment.py
SEED=20261017
OUT=tmp/sensitivity_k

run_cell () {
  local k=$1 r=$2 rho=$3
  local d=$OUT/k${k}_r${r}_rho${rho}
  if [ -f "$d/summary.json" ]; then echo "skip $d (exists)"; return; fi
  echo "start $d $(date +%T)"
  python3 "$ENGINE" \
    --samples-csv evidence/videocad/notes/confirm_set_600.csv \
    --use-all-rows --replicates 20 \
    --eps-list "$(python3 -c "print(','.join(f'{i*0.02:.2f}' for i in range(26)))")" \
    --k "$k" --budget-ratio "$r" --swap-prob 0.7 \
    --retry-repro-prob "$rho" --seed "$SEED" \
    --out-dir "$d" > "$d.log" 2>&1
  echo "done  $d $(date +%T)"
}
export -f run_cell
export ENGINE SEED OUT

# k=2 r=0.2 rho=0.9 已由 timing probe 产出一版并删除，列表中一并重跑（同种子，逐字节可复现）
JOBS=""
for k in 1 2 3; do
  for r in 0.2 0.5; do
    for rho in 0.0 0.5 0.9; do
      JOBS="$JOBS $k,$r,$rho"
    done
  done
done
# 主对照 r=0.2 优先（12 格全跑；r=0.5 为申报的附加完整性）
echo "$JOBS" | tr ' ' '\n' | grep -v '^$' | sort -t, -k2,2 | xargs -P 4 -I{} bash -c 'run_cell $(echo {} | tr "," " ")'
echo "ALL DONE $(date +%T)"
