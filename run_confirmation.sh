#!/usr/bin/env bash
# 确认集全量跑批 —— 门 v2 的判定输入。
#
# 所有实验参数在本文件内硬编码。不要通过命令行临时改参数：
# 改任何一处都会破坏预登记口径 / 配对设计（审计 docs/audit-2026-09-15-data-lineage-and-rng.md）。
#
# 前置（步骤二产物）：
#   evidence/videocad/notes/confirm_set_600.csv   600 链确认集清单（含 200/200/200 分层，与开发集不相交）
# 用法：
#   ./run_confirmation.sh <CONFIRM_SEED>
#   CONFIRM_SEED 为确认集专用种子（与开发集 20260226 不同），与抽样脚本种子一并写入论文补充材料。
set -euo pipefail
cd "$(dirname "$0")"

CONFIRM_CSV="evidence/videocad/notes/confirm_set_600.csv"
CONFIRM_SEED="${1:?用法: ./run_confirmation.sh <CONFIRM_SEED>（确认集专用种子，记录后入补充材料）}"

if [ ! -f "$CONFIRM_CSV" ]; then
  echo "缺少 $CONFIRM_CSV —— 先完成步骤二抽样（600 链，200/200/200，与开发集不相交）。"
  exit 1
fi

# 26 档网格 0→0.50 step 0.02（审计 §3.1 锁定；缩小会使 min_rules 右删失、主门失效）
EPS_LIST="$(python3 -c "print(','.join(f'{i*0.02:.2f}' for i in range(26)))")"
K=2                 # 单步重试上限（敏感性 {1,3} 另跑）
SWAP_PROB=0.7       # 注入配比（70% 动作替换 / 30% 状态翻转）

echo "== 确认集跑批: seed=$CONFIRM_SEED, grid=26pts(0..0.50), k=$K, swap=$SWAP_PROB, r∈{0.2,0.5}, ρ∈{0,0.5,0.9} =="

for R_RATIO in 0.2 0.5; do
  for RHO in 0.0 0.5 0.9; do
    rtag=$(echo "$R_RATIO" | tr -d '.')
    rhotag=$(echo "$RHO" | tr -d '.')
    out="evidence/videocad/notes/four_arm_confirm/r${rtag}_rho${rhotag}"
    echo "--> r=$R_RATIO rho=$RHO -> $out"
    python3 evidence/videocad/scripts/run_four_arm_experiment.py \
      --samples-csv "$CONFIRM_CSV" --use-all-rows \
      --replicates 20 \
      --eps-list "$EPS_LIST" \
      --k "$K" --budget-ratio "$R_RATIO" --swap-prob "$SWAP_PROB" \
      --retry-repro-prob "$RHO" \
      --seed "$CONFIRM_SEED" \
      --out-dir "$out"
    python3 scripts/analyze_fail_mix.py "$out/per_run_results.csv" --out "$out/fail_mix.csv"
  done
done

echo "== 完成。六组输出在 evidence/videocad/notes/four_arm_confirm/，接着跑 bootstrap： =="
echo "   python3 scripts/bootstrap_eps_star.py --runs evidence/videocad/notes/four_arm_confirm/r02_rho0* --plot evidence/videocad/notes/four_arm_confirm/forest_r02.png"
