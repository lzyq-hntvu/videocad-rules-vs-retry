#!/bin/bash
# swap_prob ∈ {0.3,0.5,0.7,0.9,0.95} 敏感性族重跑 —— audit §3.2⑦ 修正案（2026-09-17，运行前申报）。
#
# ⚠ 种子申报（run-once 纪律）：
#   本运行是**敏感性族新实验**，不是确认集主跑。注入种子 20261020 与确认集主跑种子
#   20261015（run-once 已封存）、消融种子 20261016、k 族种子 20261017、校验/dev 种子
#   20261018–20261019、bootstrap 种子 20260915 均不同；本族结果不进入、不影响门 v2 判定
#   （audit §3.2①/§3.2⑦）。确认集主跑（seed 20261015）已封存，本脚本不触碰任何
#   four_arm_confirm/ 既有文件（0.7 参照数字从封存确认集只读提取，见分析脚本）。
#
# 规格（照 §3.2⑦ 逐条）：confirm_set_600 --use-all-rows（600 链），replicates 20，
#   判据 0.5，26 点 ε 网格 0→0.50（引擎默认），四臂，k=2，r ∈ {0.2,0.5}，
#   ρ ∈ {0,0.5,0.9}，swap_prob ∈ {0.3,0.5,0.7,0.9,0.95}（0.7 为族内参照点，
#   论文基准数字仍取封存确认集 seed 20261015）。
# 规模：5 × 6 × 1,248,000 = 37,440,000 runs。
# 输出：per_run 大表留 tmp/sensitivity_swap/（可经本脚本字节级复现）；
#   小件（curve_summary/eps_star/summary.json）+ 格日志复制入
#   evidence/videocad/notes/sensitivity_swap/sp{SP}_r{R}_rho{RHO}/。
#   bootstrap（B=9999，种子 20261021）由 analyze_swap_sensitivity.py 完成。
set -u
cd "$(dirname "$0")/../../.."   # repo root
ENGINE=evidence/videocad/scripts/run_four_arm_experiment.py
SEED=20261020
OUT=tmp/sensitivity_swap
NOTES=evidence/videocad/notes/sensitivity_swap

run_cell () {
  local sp=$1 r=$2 rho=$3
  local d=$OUT/sp${sp}_r${r}_rho${rho}
  if [ -f "$d/summary.json" ]; then echo "skip $d (exists)"; return; fi
  mkdir -p "$d"   # 先建目录：日志重定向发生在引擎建目录之前
  echo "start $d $(date +%T)"
  python3 "$ENGINE" \
    --samples-csv evidence/videocad/notes/confirm_set_600.csv \
    --use-all-rows --replicates 20 \
    --eps-list "$(python3 -c "print(','.join(f'{i*0.02:.2f}' for i in range(26)))")" \
    --k 2 --budget-ratio "$r" --swap-prob "$sp" \
    --retry-repro-prob "$rho" --seed "$SEED" \
    --success-criterion 0.5 \
    --out-dir "$d" > "$d.log" 2>&1
  echo "done  $d $(date +%T)"
}
export -f run_cell
export ENGINE SEED OUT

JOBS=""
for sp in 0.3 0.5 0.7 0.9 0.95; do
  for r in 0.2 0.5; do
    for rho in 0.0 0.5 0.9; do
      JOBS="$JOBS $sp,$r,$rho"
    done
  done
done
# 主对照 r=0.2 优先（30 格全跑；r=0.5 为申报的附加完整性）
echo "$JOBS" | tr ' ' '\n' | grep -v '^$' | sort -t, -k2,2 | xargs -P 6 -I{} bash -c 'run_cell $(echo {} | tr "," " ")'

# 小件复制入 notes（per_run 大表留 tmp）
for sp in 0.3 0.5 0.7 0.9 0.95; do
  for r in 0.2 0.5; do
    for rho in 0.0 0.5 0.9; do
      d=$OUT/sp${sp}_r${r}_rho${rho}
      n=$NOTES/sp${sp}_r${r}_rho${rho}
      if [ -f "$d/summary.json" ]; then
        mkdir -p "$n"
        cp "$d/curve_summary.csv" "$d/eps_star.csv" "$d/summary.json" "$n/"
        cp "$d.log" "$n/"
      fi
    done
  done
done
echo "ALL DONE $(date +%T)"
