# videocad-rules-vs-retry · 常用目标
# 实验参数的唯一权威来源是 run_confirmation.sh 与引擎默认值（预登记口径）；
# 本文件只做编排，不承载参数。

PY = python3
CONFIRM_CSV = evidence/videocad/notes/confirm_set_600.csv

.PHONY: help confirm bootstrap-confirm bootstrap-dev dev-rho-sweep parity clean-tmp

help:
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-18s %s\n", $$1, $$2}'

confirm: ## 确认集全量跑批（需先完成步骤二抽样；用法: make confirm SEED=<确认集种子>）
	@test -n "$(SEED)" || { echo "缺少 SEED：make confirm SEED=<确认集专用种子>"; exit 1; }
	./run_confirmation.sh $(SEED)

bootstrap-confirm: ## 确认集 ε* bootstrap + 森林图（门 v2 判定输入）
	$(PY) scripts/bootstrap_eps_star.py --runs evidence/videocad/notes/four_arm_confirm/r02_rho00 \
		evidence/videocad/notes/four_arm_confirm/r02_rho05 \
		evidence/videocad/notes/four_arm_confirm/r02_rho09 \
		--plot evidence/videocad/notes/four_arm_confirm/forest_r02.png

bootstrap-dev: ## 开发集 bootstrap 验证（9 格 + 主格 + 森林图）
	$(PY) scripts/bootstrap_eps_star.py --runs tmp/dev_ext_r02_rho00 tmp/dev_ext_r02_rho05 tmp/dev_ext_r02_rho09 \
		--plot tmp/dev_ext_forest_r02.png

dev-rho-sweep: ## 开发集 ρ 扫描（r=0.2，26 档网格）
	for rho in 0.0 0.5 0.9; do \
	  $(PY) evidence/videocad/scripts/run_four_arm_experiment.py --per-label 30 --replicates 40 \
	    --k 2 --budget-ratio 0.2 --retry-repro-prob $$rho --seed 20260226 \
	    --out-dir tmp/dev_ext_r02_rho$$(echo $$rho | tr -d '.'); \
	done

parity: ## 旧管线逐字节复现验证
	$(PY) evidence/videocad/scripts/run_h2_h3_mechanism_proxy.py --out-dir tmp/dev_repro_old
	diff tmp/dev_repro_old/curve_summary.csv evidence/videocad/notes/h2_h3_proxy_experiment/curve_summary.csv
	diff tmp/dev_repro_old/per_run_results.csv evidence/videocad/notes/h2_h3_proxy_experiment/per_run_results.csv
	@echo "PARITY OK"

clean-tmp: ## 清理 tmp/（git 忽略的临时输出）
	rm -rf tmp/*
