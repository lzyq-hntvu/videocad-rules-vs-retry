#!/usr/bin/env bash
# 确认集全量跑批 —— 门 v2 的判定输入。只运行一次。
#
# 所有实验参数在本文件内硬编码。不要通过命令行临时改参数：
# 改任何一处都会破坏预登记口径 / 配对设计（审计 docs/audit-2026-09-15-data-lineage-and-rng.md）。
#
# 确认集注入种子 CONFIRM_RUN_SEED = 20261015 —— 预登记于审计 §3.2（2026-09-16 批准时锁死），
# 不得以更换种子重跑。崩溃恢复：删除半成品输出目录后用同种子重跑（结果逐字节一致）。
set -euo pipefail
cd "$(dirname "$0")"

CONFIRM_CSV="evidence/videocad/notes/confirm_set_600.csv"
CONFIRM_RUN_SEED=20261015
DONE_MARKER="evidence/videocad/notes/four_arm_confirm/RUN_COMPLETE"

if [ -f "$DONE_MARKER" ] && [ "${ALLOW_RERUN:-0}" != "1" ]; then
  echo "阻断：$DONE_MARKER 已存在——确认集只运行一次（审计 §3.2 预登记）。"
  echo "若确知前次为崩溃残留且已清除半成品，用 ALLOW_RERUN=1 ./run_confirmation.sh 同种子续跑。"
  exit 1
fi

if [ ! -f "$CONFIRM_CSV" ]; then
  echo "缺少 $CONFIRM_CSV —— 先 make sample-confirm（600 链，200/200/200，与开发集不相交）。"
  exit 1
fi

# 26 档网格 0→0.50 step 0.02（审计 §3.1 锁定；缩小会使 min_rules 右删失、主门失效）
EPS_LIST="$(python3 -c "print(','.join(f'{i*0.02:.2f}' for i in range(26)))")"
K=2                 # 单步重试上限（敏感性 {1,3} 另跑）
SWAP_PROB=0.7       # 注入配比（70% 动作替换 / 30% 状态翻转）

echo "== 确认集跑批（一次）: seed=$CONFIRM_RUN_SEED, grid=26pts(0..0.50), k=$K, swap=$SWAP_PROB, r∈{0.2,0.5}, ρ∈{0,0.5,0.9} =="

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
      --seed "$CONFIRM_RUN_SEED" \
      --out-dir "$out"
    python3 scripts/analyze_fail_mix.py "$out/per_run_results.csv" --out "$out/fail_mix.csv"
  done
done

date -Is > "$DONE_MARKER"
echo "== 完成（marker: $DONE_MARKER）。接着：make bootstrap-confirm 判门 v2 =="
