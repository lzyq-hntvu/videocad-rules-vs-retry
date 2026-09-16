# videocad-rules-vs-retry · 常用目标
# 实验参数的唯一权威来源是 run_confirmation.sh 与引擎默认值（预登记口径）；
# 本文件只做编排，不承载参数。

PY = python3
CONFIRM_CSV = evidence/videocad/notes/confirm_set_600.csv

.PHONY: help confirm bootstrap-confirm bootstrap-confirm-all bootstrap-dev dev-rho-sweep parity sample-confirm supp-bundle clean-tmp

help:
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-18s %s\n", $$1, $$2}'

sample-confirm: ## 步骤二：确认集 600 链抽样（种子 20260916 已锁定）
	$(PY) scripts/sample_confirm_set.py

confirm: ## 确认集全量跑批（种子 20261015 已在 §3.2 预登记；只运行一次）
	./run_confirmation.sh

bootstrap-confirm: ## 确认集 ε* bootstrap：r=0.2 三目录（门 v2 判定输入，含 9 格 + 主格 + 对照量）
	$(PY) scripts/bootstrap_eps_star.py --runs evidence/videocad/notes/four_arm_confirm/r02_rho00 \
		evidence/videocad/notes/four_arm_confirm/r02_rho05 \
		evidence/videocad/notes/four_arm_confirm/r02_rho09 \
		--out-prefix evidence/videocad/notes/four_arm_confirm/bootstrap_r02 \
		--plot evidence/videocad/notes/four_arm_confirm/forest_r02.png

bootstrap-confirm-all: ## 确认集 bootstrap 全量（r=0.2 + r=0.5 敏感性族，供承重项正文报告）
	$(PY) scripts/bootstrap_eps_star.py --runs evidence/videocad/notes/four_arm_confirm/r02_rho00 \
		evidence/videocad/notes/four_arm_confirm/r02_rho05 \
		evidence/videocad/notes/four_arm_confirm/r02_rho09 \
		evidence/videocad/notes/four_arm_confirm/r05_rho00 \
		evidence/videocad/notes/four_arm_confirm/r05_rho05 \
		evidence/videocad/notes/four_arm_confirm/r05_rho09 \
		--out-prefix evidence/videocad/notes/four_arm_confirm/bootstrap_all \
		--plot evidence/videocad/notes/four_arm_confirm/forest_all.png

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

supp-bundle: ## 打包论文补充材料（tmp/supplementary_bundle.zip）
	@rm -f tmp/supplementary_bundle.zip
	zip -q -r tmp/supplementary_bundle.zip \
	  evidence/videocad/scripts/run_four_arm_experiment.py \
	  evidence/videocad/scripts/run_h2_h3_mechanism_proxy.py \
	  scripts/sample_confirm_set.py scripts/bootstrap_eps_star.py \
	  scripts/eps_star_grid_summary.py scripts/analyze_fail_mix.py \
	  run_confirmation.sh Makefile .gitignore \
	  docs/experiment-plan-v1.md docs/audit-2026-09-15-data-lineage-and-rng.md \
	  docs/paper-writing-notes.md docs/zenodo-submission-checklist.md \
	  LICENSE README.md \
	  evidence/videocad/notes/confirm_set_600.csv \
	  evidence/videocad/notes/confirm_set_600_sampling_record.json \
	  evidence/videocad/notes/four_arm_confirm/*/curve_summary.csv \
	  evidence/videocad/notes/four_arm_confirm/*/eps_star.csv \
	  evidence/videocad/notes/four_arm_confirm/*/fail_mix.csv \
	  evidence/videocad/notes/four_arm_confirm/*/summary.json \
	  evidence/videocad/notes/four_arm_confirm/exploratory_rho0_rscan/ \
	  evidence/videocad/notes/four_arm_confirm/bootstrap_r02_results.csv \
	  evidence/videocad/notes/four_arm_confirm/bootstrap_r05_results.csv \
	  evidence/videocad/notes/four_arm_confirm/eps_star_range.csv \
	  evidence/videocad/notes/four_arm_confirm/fig_eps_star_vs_rho.png \
	  evidence/videocad/notes/four_arm_confirm/forest_r02.png \
	  evidence/videocad/notes/four_arm_dev_grid_ext/bootstrap_results_dev.csv \
	  evidence/videocad/notes/four_arm_dev_grid_ext/forest_r02_dev.png
	@unzip -l tmp/supplementary_bundle.zip | tail -2
	@echo "bundle ready: tmp/supplementary_bundle.zip （per_run 大表单独上传，见 zenodo-submission-checklist.md）"

clean-tmp: ## 清理 tmp/（git 忽略的临时输出）
	rm -rf tmp/*
