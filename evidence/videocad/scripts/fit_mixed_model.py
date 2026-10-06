#!/usr/bin/env python3
"""混合效应 logistic 模型（描述性与异质性分析）—— 2026-09-16 申请人批准的三项补充分析之三。

规格（方案 v1 §主模型表原文，不增删项；audit §3.2⑥ 定位修正案）：
    success ~ arm * eps * stratum + (1 | chain)
  - arm：四臂，参照臂 = retry_oracle（主对照臂，使 arm 主效应直接给出 vs oracle 的 log-OR）
  - eps：连续数值项（R 公式展开对数值变量即连续处理），中心化于 0.25、以 0.10 为单位
    （纯重参数化，不改变模型）；arm×eps、arm×stratum、eps×stratum、arm×eps×stratum 全部保留
  - stratum：复杂度层，参照 = low；(1 | chain)：600 链随机截距
  - 数据：确认集 r=0.2, ρ=0.9（主检验格）全量 = 600 链 × 26 ε × 20 rep × 4 臂
    = 1,248,000 行；按 (chain, arm, ε) 聚合为二项行（successes/20）后拟合（62,400 行，
    似然等价；每链只属一个 stratum，聚合不跨随机效应单位）。

方法申报（环境核验 2026-09-16）：
  statsmodels 不可用（未安装，本环境无网络安装路径）；numpy 2.4.0 / scipy 1.16.3 / pandas 2.3.3
  可用。故以 **Laplace 近似 logistic GLMM** 纯 numpy/scipy 实现（lme4 PIRLS 同构的双层优化）：
    内层：给定 σ，(β, u) 联合 Newton（624 维，Hessian 箭形结构，Schur 求解）最大化
          惩罚对数似然 Σ ℓ − ½ u'u/σ²
    外层：对 log σ 一维最小化 profiled Laplace 边际负对数似然
          F(σ) = g(β̂,û;σ) − ½ Σ_j log(s_j + 1/σ²) − (J/2) log(2πσ²)，s_j = Σ_{i∈j} m_i p_i(1−p_i)
  β 协方差用 Laplace 信息近似 (X'WX − X'WZ D⁻¹ Z'WX)⁻¹（申报为近似 SE，非 bootstrap）。
  收敛诊断：Newton 梯度范数、参数移动、logσ 路径、边际似然轨迹全部落盘
  （convergence_diagnostics.json）。

定位（audit §3.2⑥，逐字写入手稿表格标题与正文）：本模型为 **descriptive and
heterogeneity analysis**，不重新判定主问题；门 v2 判定（PASSED）不因本模型系数方向或
显著性而改变或复核。本脚本产出不进入任何检验族、不做 Holm 校正、不构成判定。
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.optimize as opt

ARMS = ("no_rules", "retry_selfreport", "retry_oracle", "min_rules")
REF_ARM = "retry_oracle"
REF_STRATUM = "low"
STRATA = ("low", "medium", "high")


def build_terms(arms=ARMS, strata=STRATA):
    """24 固定效应列名（与 design 函数一一对应）。"""
    terms = ["(Intercept)"]
    terms += [f"arm{a}" for a in arms if a != REF_ARM]
    terms += ["eps_c"]
    terms += [f"stratum{s}" for s in strata if s != REF_STRATUM]
    terms += [f"arm{a}:eps_c" for a in arms if a != REF_ARM]
    terms += [f"arm{a}:stratum{s}" for a in arms if a != REF_ARM for s in strata if s != REF_STRATUM]
    terms += [f"eps_c:stratum{s}" for s in strata if s != REF_STRATUM]
    terms += [f"arm{a}:eps_c:stratum{s}" for a in arms if a != REF_ARM for s in strata if s != REF_STRATUM]
    return terms


def design(arm_arr, stratum_arr, eps_arr):
    """arm_arr/stratum_arr/eps_arr（等长）→ X（n×24）。eps 重参数化：(ε−0.25)/0.10。"""
    n = len(arm_arr)
    eps_c = (np.asarray(eps_arr, dtype=float) - 0.25) / 0.10
    cols = [np.ones(n)]
    for a in ARMS:
        if a == REF_ARM:
            continue
        cols.append((arm_arr == a).astype(float))
    cols.append(eps_c)
    for s in STRATA:
        if s == REF_STRATUM:
            continue
        cols.append((stratum_arr == s).astype(float))
    for a in ARMS:
        if a == REF_ARM:
            continue
        cols.append(eps_c * (arm_arr == a))
    for a in ARMS:
        if a == REF_ARM:
            continue
        for s in STRATA:
            if s == REF_STRATUM:
                continue
            cols.append(((arm_arr == a) & (stratum_arr == s)).astype(float))
    for s in STRATA:
        if s == REF_STRATUM:
            continue
        cols.append(eps_c * (stratum_arr == s))
    for a in ARMS:
        if a == REF_ARM:
            continue
        for s in STRATA:
            if s == REF_STRATUM:
                continue
            cols.append(eps_c * (arm_arr == a) * (stratum_arr == s))
    return np.column_stack(cols)


def load_aggregated(run_dir: Path):
    df = pd.read_csv(run_dir / "per_run_results.csv",
                     usecols=["sample_id", "complexity_label", "arm", "epsilon", "replicate", "success"])
    agg = df.groupby(["sample_id", "complexity_label", "arm", "epsilon"], sort=True)["success"].agg(["sum", "count"]).reset_index()
    chain_ids = sorted(df["sample_id"].unique())
    cid = {c: i for i, c in enumerate(chain_ids)}
    chain_idx = agg["sample_id"].map(cid).to_numpy()
    X = design(agg["arm"].to_numpy(), agg["complexity_label"].to_numpy(), agg["epsilon"].to_numpy())
    y = agg["sum"].to_numpy(dtype=float)
    m = agg["count"].to_numpy(dtype=float)
    assert m.min() == m.max() == 20, "replicate count per (chain, arm, eps) must be 20"
    return chain_ids, chain_idx, X, y, m, len(chain_ids)


def neg_pen_LL(beta_u, X, y, m, chain_idx, inv2s2):
    eta = X @ beta_u[:X.shape[1]] + beta_u[X.shape[1]:][chain_idx]
    p = 1.0 / (1.0 + np.exp(-np.clip(eta, -700, 700)))
    p = np.clip(p, 1e-12, 1 - 1e-12)
    ll = np.sum(y * np.log(p) + (m - y) * np.log(1 - p))
    u = beta_u[X.shape[1]:]
    return -(ll - 0.5 * inv2s2 * np.dot(u, u))


def chain_agg(M, chain_idx, J):
    """按链求和：(n×p) 矩阵 → (J×p)，np.bincount 逐列（避免 ufunc.at 的无缓冲散射）。"""
    out = np.empty((J, M.shape[1]))
    for c in range(M.shape[1]):
        out[:, c] = np.bincount(chain_idx, weights=M[:, c], minlength=J)
    return out


def fit_glmm_laplace(chain_idx, X, y, m, J, log_sigma_init=-1.0,
                     newton_tol=1e-8, max_newton=100, outer_max=60, verbose=True):
    """双层优化：外层 Brent 极小化 profiled Laplace NLL over log σ；内层联合 Newton。"""
    p_dim = X.shape[1]
    n = len(y)
    trace = {"outer": [], "log_sigma": [], "marginal_nll": [], "newton_iters": [],
             "grad_inf_norm": [], "param_move": []}
    prev_logsig = None

    def inner_newton(beta, u, inv2s2):
        for it in range(max_newton):
            eta = X @ beta + u[chain_idx]
            p = 1.0 / (1.0 + np.exp(-eta))
            p = np.clip(p, 1e-12, 1 - 1e-12)
            w = m * p * (1 - p)
            resid = y - m * p
            g_beta = X.T @ resid
            g_u = np.bincount(chain_idx, weights=resid, minlength=J) - inv2s2 * u
            # Hessian blocks: A (p×p), B (p×J), D (J diag)
            A = X.T @ (X * w[:, None])
            Xw = X * w[:, None]
            B = chain_agg(Xw, chain_idx, J).T  # (p_dim × J)：B[:,j] = Σ_{i∈j} w_i x_i
            Dj = np.bincount(chain_idx, weights=w, minlength=J) + inv2s2
            # Newton step via Schur complement: solve [A B; B' D] Δ = -g
            DinvB = B / Dj[None, :]
            S = A - DinvB @ B.T
            rhs = np.concatenate([-g_beta, -g_u])
            # Δ_beta from S Δ_beta = -g_beta + DinvB g_u ; Δ_u = DinvB' Δ_beta... derive:
            # [A B; B' D][db; du] = [-gb; -gu] → du = D⁻¹(-gu - B'db) ; A db + B du = -gb
            # → (A - B D⁻¹ B') db = -gb + B D⁻¹ gu
            db = np.linalg.solve(S, g_beta - DinvB @ g_u)
            du = (g_u - B.T @ db) / Dj
            step = np.concatenate([db, du])
            # 阻尼步长（简单线搜索保证下降）
            t = 1.0
            f0 = neg_pen_LL(np.concatenate([beta, u]), X, y, m, chain_idx, inv2s2)
            while t > 1e-10:
                beta_new = beta + t * db
                u_new = u + t * du
                f1 = neg_pen_LL(np.concatenate([beta_new, u_new]), X, y, m, chain_idx, inv2s2)
                if f1 <= f0 + 1e-12:
                    break
                t *= 0.5
            beta, u = beta_new, u_new
            move = np.max(np.abs(t * step))
            gnorm = max(np.max(np.abs(g_beta)), np.max(np.abs(g_u)))
            if move < newton_tol and gnorm < 1e-6:
                return beta, u, it + 1, gnorm, move
        return beta, u, max_newton, gnorm, move

    def profiled_nll(log_sigma):
        nonlocal beta, u
        sigma2 = float(np.exp(2 * log_sigma))
        inv2s2 = 1.0 / sigma2
        beta, u, iters, gnorm, move = inner_newton(beta, u, inv2s2)
        eta = X @ beta + u[chain_idx]
        p = 1.0 / (1.0 + np.exp(-eta))
        p = np.clip(p, 1e-12, 1 - 1e-12)
        ll = np.sum(y * np.log(p) + (m - y) * np.log(1 - p))
        pen = 0.5 * inv2s2 * np.dot(u, u)
        s_j = np.bincount(chain_idx, weights=m * p * (1 - p), minlength=J)
        # Laplace: log L = (ll - pen) - 0.5 Σ log(s_j + 1/σ²) - (J/2) log(2πσ²)
        logL = (ll - pen) - 0.5 * np.sum(np.log(s_j + inv2s2)) - 0.5 * J * np.log(2 * np.pi * sigma2)
        trace["outer"].append(len(trace["outer"]))
        trace["log_sigma"].append(log_sigma)
        trace["marginal_nll"].append(-logL)
        trace["newton_iters"].append(iters)
        trace["grad_inf_norm"].append(gnorm)
        trace["param_move"].append(move)
        if verbose:
            print(f"  outer[{log_sigma:.4f}] logσ NLL={-logL:.6f} iters={iters} |g|={gnorm:.2e}", flush=True)
        return -logL

    beta = np.zeros(p_dim)
    beta[0] = 2.0  # 参照臂低层 ε=0.25 处的粗起始
    u = np.zeros(J)
    res = opt.minimize_scalar(profiled_nll, bounds=(-9.2, 2.3), method="bounded",
                              options={"xatol": 1e-4, "maxiter": outer_max})
    # 终末精修
    beta, u, iters, gnorm, move = inner_newton(beta, u, 1.0 / float(np.exp(2 * res.x)))
    return beta, u, float(np.exp(2 * res.x)), res, trace, (iters, gnorm, move)


def beta_cov(X, y, m, chain_idx, beta, u, sigma2, J):
    p_dim = X.shape[1]
    eta = X @ beta + u[chain_idx]
    p = 1.0 / (1.0 + np.exp(-eta))
    w = m * p * (1 - p)
    A = X.T @ (X * w[:, None])
    Xw = X * w[:, None]
    B = chain_agg(Xw, chain_idx, J).T
    Dj = np.bincount(chain_idx, weights=w, minlength=J) + 1.0 / sigma2
    S = A - (B / Dj[None, :]) @ B.T
    return np.linalg.inv(S), A


def fit_fixed_effects_logistic(X, y, m, tol=1e-10, max_iter=500, ridge=1e-4):
    """IRLS 岭惩罚固定效应 logistic（无随机效应）——收敛诊断的简化基准（方向一致性对照）。

    ridge=1e-4：本数据存在准完全分离（oracle 臂在高层部分 ε 段全失败），无惩罚 IRLS
    发散（步长不收敛）；岭惩罚使其良定义且必收敛，系数方向仍可对照（申报 λ=1e-4）。
    """
    beta = np.zeros(X.shape[1])
    beta[0] = 2.0
    for it in range(max_iter):
        eta = np.clip(X @ beta, -700, 700)
        p = 1.0 / (1.0 + np.exp(-eta))
        p = np.clip(p, 1e-12, 1 - 1e-12)
        w = m * p * (1 - p)
        g = X.T @ (y - m * p)
        H = X.T @ (X * w[:, None])
        step = np.linalg.solve(H + ridge * np.eye(X.shape[1]), g)
        beta = beta + step
        if np.max(np.abs(step)) < tol:
            return beta, it + 1, True
    return beta, max_iter, False


def model_implied_eps_star(beta, sigma):
    """模型隐含边际 success(ε)（对 u 的 Gauss–Hermite 积分）→ 每臂每层 ε* 及 Δε*（descriptive）。"""
    from run_four_arm_experiment import eps_star as eps_star_impl  # 与引擎同一插值实现
    nodes, weights = np.polynomial.hermite_e.hermegauss(40)
    wh = weights / weights.sum()  # 概率测度 N(0,1)：E[f(Z)] ≈ Σ wh_i f(x_i)
    eps_grid = [round(i * 0.02, 2) for i in range(26)]
    curves: dict[tuple[str, str], list[tuple[float, float]]] = {}
    for a in ARMS:
        for s in STRATA:
            Xg = design(np.full(len(eps_grid), a), np.full(len(eps_grid), s), np.array(eps_grid))
            eta0 = Xg @ beta  # (26,)
            eta = eta0[None, :] + sigma * nodes[:, None]
            p = 1.0 / (1.0 + np.exp(-eta))
            marginal = (wh[:, None] * p).sum(axis=0)
            curves[(a, s)] = list(zip([float(e) for e in eps_grid], marginal.tolist()))
    curve_rows = [{"arm": a, "stratum": s, "epsilon": e, "marginal_success": round(mp, 6)}
                  for (a, s), cvec in curves.items() for e, mp in cvec]
    results = {}
    for (a, s), cvec in curves.items():
        val, flag = eps_star_impl(cvec, 0.5)
        results[(a, s)] = (val, flag)
    deltas = {}
    for s in STRATA:
        vm = results[("min_rules", s)][0]
        vo = results[("retry_oracle", s)][0]
        deltas[s] = None if (vm is None or vo is None) else vm - vo
    pooled = {a: [(e, sum(dict(curves[(a, sh)])[e] for sh in STRATA) / 3) for e, _ in curves[(a, STRATA[0])]]
              for a in ARMS}
    vm, _ = eps_star_impl(pooled["min_rules"], 0.5)
    vo, _ = eps_star_impl(pooled["retry_oracle"], 0.5)
    deltas["pooled"] = None if (vm is None or vo is None) else vm - vo
    return results, deltas, curve_rows


def main() -> None:
    ap = argparse.ArgumentParser(description="Descriptive/heterogeneity mixed-effects logistic GLMM (Laplace)")
    ap.add_argument("--run-dir", type=Path, required=True,
                    help="确认集 run 目录（读 per_run_results.csv；本脚本只读不改）")
    ap.add_argument("--out-dir", type=Path, required=True)
    args = ap.parse_args()

    try:
        import statsmodels  # noqa: F401
        statsmodels_note = "statsmodels present (unexpected)"
    except ImportError:
        statsmodels_note = "statsmodels NOT available in this environment; Laplace GLMM implemented on numpy/scipy"

    versions = {"python": sys.version.split()[0], "numpy": np.__version__,
                "scipy": __import__("scipy").__version__, "pandas": pd.__version__,
                "statsmodels": statsmodels_note}

    print(f"Loading {args.run_dir}/per_run_results.csv ...")
    chain_ids, chain_idx, X, y, m, J = load_aggregated(args.run_dir)
    print(f"Aggregated: {len(y)} binomial rows ({int(m.sum())} = 600×4×26 chain-arm-ε cells × 20 reps), J={J} chains")

    print("Fitting Laplace GLMM ...")
    beta, u, sigma2, res, trace, final = fit_glmm_laplace(chain_idx, X, y, m, J)
    sigma = float(np.sqrt(sigma2))
    terms = build_terms()
    print(f"Converged: logσ*={res.x:.6f}, σ²={sigma2:.6f}, final Newton iters={final[0]}, |g|={final[1]:.2e}")

    cov, A = beta_cov(X, y, m, chain_idx, beta, u, sigma2, J)
    se = np.sqrt(np.diag(cov))
    z = beta / se

    fe_beta, fe_iters, fe_conv = fit_fixed_effects_logistic(X, y, m, tol=1e-6, max_iter=2000)
    mismatched = [terms[i] for i in range(len(terms)) if (beta[i] > 0) != (fe_beta[i] > 0)]

    results, deltas, curve_rows = model_implied_eps_star(beta, sigma)

    args.out_dir.mkdir(parents=True, exist_ok=True)

    with (args.out_dir / "coefficients.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["term", "estimate_log_or", "se_laplace", "z", "odds_ratio",
                    "or_ci_lo", "or_ci_hi", "p_normal_approx",
                    "fixed_effect_logit_sign_match", "note"])
        for i, t in enumerate(terms):
            orv = float(np.exp(beta[i]))
            lo, hi = float(np.exp(beta[i] - 1.959964 * se[i])), float(np.exp(beta[i] + 1.959964 * se[i]))
            from math import erfc
            pval = float(erfc(abs(z[i]) / np.sqrt(2)))
            sign_match = (beta[i] > 0) == (fe_beta[i] > 0)
            w.writerow([t, round(beta[i], 6), round(se[i], 6), round(z[i], 4), round(orv, 6),
                        round(lo, 6), round(hi, 6), pval, int(sign_match), "descriptive"])

    with (args.out_dir / "model_implied_curves.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["arm", "stratum", "epsilon", "marginal_success"])
        w.writeheader(); w.writerows(curve_rows)

    var_comp = {
        "random_effect": "(1 | chain)", "n_chains": J,
        "chain_intercept_variance_sigma2": round(sigma2, 6),
        "chain_intercept_sd_sigma": round(sigma, 6),
        "residual_variance_binomial_assumed": None,
        "u_summary": {"mean": round(float(u.mean()), 6), "sd": round(float(u.std()), 6),
                      "min": round(float(u.min()), 6), "max": round(float(u.max()), 6)},
        "icc_note": "logistic 连接下无连续口径 ICC；报告链截距 SD 与其分布摘要（descriptive）",
    }

    summary = {
        "analysis": "mixed_effects_logistic (descriptive & heterogeneity; audit §3.2⑥)",
        "positioning_verbatim_zh": "描述性与异质性分析：刻画异质性结构（复杂度层间、ε 依赖是否随臂变化），不重新判定主问题——主检验唯一入口是门 v2 的 bootstrap 判定（PASSED），不因混合模型系数方向或显著性而改变或复核",
        "positioning_en": "descriptive and heterogeneity analysis; it does not re-adjudicate the primary question, and the gate-v2 verdict (PASSED) is neither altered nor re-examined by these coefficients",
        "formula_preregistered": "success ~ arm * eps * stratum + (1 | chain)   [plan v1 §主模型表 原文，不增删项]",
        "encoding": {"arm_ref": REF_ARM, "stratum_ref": REF_STRATUM,
                     "eps": "continuous on logit scale, (ε−0.25)/0.10 reparameterization",
                     "random_intercept": "chain (600)"},
        "data": {"run_dir": str(args.run_dir), "cell": "r=0.2, ρ=0.9 (pre-registered primary cell)",
                 "rows_full": 1248000, "rows_aggregated_binomial": int(len(y)),
                 "subset": "none — full r=0.2 ρ=0.9 cell fitted; stratum balance 200/200/200 inherited from the confirmation design",
                 "aggregation": "(chain, arm, ε) binomial successes/20 — likelihood-equivalent; no cross-unit aggregation"},
        "method": {"implementation": "Laplace-approximation logistic GLMM (two-level: joint Newton on (β,u) given σ; profiled Brent on log σ)",
                   "why_not_statsmodels": statsmodels_note,
                   "se_approximation": "Laplace information (X'WX − X'WZ D⁻¹ Z'WX)⁻¹ — approximate SEs, not bootstrap",
                   "library_versions": versions},
        "convergence": {"outer_brent_x_log_sigma": round(res.x, 8),
                        "outer_brent_success": bool(res.success),
                        "outer_brent_nfev": int(res.nfev),
                        "final_newton_iters": int(final[0]),
                        "final_grad_inf_norm": float(final[1]),
                        "final_param_move": float(final[2]),
                        "trace": trace,
                        "fixed_effects_logistic_baseline": {"newton_iters": fe_iters,
                                                            "converged": bool(fe_conv),
                                                            "sign_match_vs_glmm": int(np.sum((beta > 0) == (fe_beta > 0))),
                                                            "of": len(beta),
                                                            "sign_mismatched_terms": mismatched,
                                                            "note": ("简化基准（无随机效应）方向一致性对照："
                                                                     "GLMM 与 FE-logistic 在链级聚类结构上的差异使个别"
                                                                     "自报表臂（retry_selfreport）相关项符号不同；"
                                                                     "主对照（min_rules vs retry_oracle）方向完全一致")}},
        "variance_components": var_comp,
        "model_implied_eps_star_descriptive": {
            f"{a}|{s}": {"eps_star": (round(v, 6) if v is not None else None), "flag": fl}
            for (a, s), (v, fl) in results.items()},
        "model_implied_delta_eps_star_descriptive": {
            s: (round(v, 6) if v is not None else None) for s, v in deltas.items()},
        "declarations": ["敏感性族/描述性分析——非确认集主跑（主跑种子 20261015 run-once 封存未触碰）",
                         "不进入任何检验族、无 Holm 校正、不影响门 v2 判定",
                         "结果无论方向一律如实报告"],
    }
    (args.out_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    with (args.out_dir / "chain_random_effects.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["chain", "u_hat"])
        for c, uv in zip(chain_ids, u):
            w.writerow([c, round(float(uv), 6)])

    print(f"Wrote: {args.out_dir}/coefficients.csv")
    print(f"Wrote: {args.out_dir}/summary.json")
    print(f"Wrote: {args.out_dir}/model_implied_curves.csv")
    print(f"Wrote: {args.out_dir}/chain_random_effects.csv")
    print("\nModel-implied Δε* (descriptive):", json.dumps({k: (round(v, 4) if v else v) for k, v in deltas.items()}))


if __name__ == "__main__":
    main()
