"""Controlled multi-seed experiment runner and statistical comparison (mean, variance, 95% CI)."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
from scipy import stats

from eidolon.core.engine import ExperimentConfig, SimulationEngine

COMPARE_METRICS: tuple[str, ...] = (
    "cooperation_index",
    "gini_coefficient",
    "mean_trust",
    "network_density",
    "community_count",
    "institution_count",
    "cultural_diversity",
    "mean_q_value",
    "trade_volume",
    "collective_success_rate",
    "avg_need_satisfaction",
)


def summarize_samples(values: list[float]) -> dict[str, float]:
    n = len(values)
    if n == 0:
        return {"n": 0, "mean": 0.0, "variance": 0.0, "std": 0.0, "ci95_low": 0.0, "ci95_high": 0.0}
    arr = np.array(values, dtype=np.float64)
    mean = float(np.mean(arr))
    if n == 1:
        return {"n": 1, "mean": round(mean, 4), "variance": 0.0, "std": 0.0, "ci95_low": round(mean, 4), "ci95_high": round(mean, 4)}
    var = float(np.var(arr, ddof=1))
    std = math.sqrt(var)
    se = std / math.sqrt(n)
    t_crit = float(stats.t.ppf(0.975, df=n - 1))
    margin = t_crit * se
    return {
        "n": n,
        "mean": round(mean, 4),
        "variance": round(var, 6),
        "std": round(std, 4),
        "ci95_low": round(mean - margin, 4),
        "ci95_high": round(mean + margin, 4),
    }


def run_controlled_comparison(
    config_a: ExperimentConfig,
    config_b: ExperimentConfig,
    seeds: list[int] | None = None,
    ticks: int = 80,
) -> dict[str, Any]:
    """Run paired multi-seed trials for Experiment A vs Experiment B and compute statistical differences."""
    trial_seeds = seeds or [42, 101, 202]
    results_a: dict[str, list[float]] = {m: [] for m in COMPARE_METRICS}
    results_b: dict[str, list[float]] = {m: [] for m in COMPARE_METRICS}

    for idx, s in enumerate(trial_seeds):
        cfg_a = ExperimentConfig.from_dict({**config_a.to_dict(), "seed": s})
        cfg_b = ExperimentConfig.from_dict({**config_b.to_dict(), "seed": s})

        eng_a = SimulationEngine(f"cmp_a_{idx}", cfg_a)
        eng_b = SimulationEngine(f"cmp_b_{idx}", cfg_b)

        for _ in range(ticks):
            eng_a.step()
            eng_b.step()

        last_a = eng_a.metrics_history[-1]
        last_b = eng_b.metrics_history[-1]
        for m in COMPARE_METRICS:
            results_a[m].append(float(last_a[m]))
            results_b[m].append(float(last_b[m]))

    comparison: dict[str, Any] = {}
    for m in COMPARE_METRICS:
        sa = summarize_samples(results_a[m])
        sb = summarize_samples(results_b[m])
        diff = sb["mean"] - sa["mean"]
        p_val = 1.0
        if len(trial_seeds) >= 2:
            _, p_raw = stats.ttest_rel(results_b[m], results_a[m])
            if not math.isnan(float(p_raw)):
                p_val = float(p_raw)
        comparison[m] = {
            "experiment_a": sa,
            "experiment_b": sb,
            "mean_diff_b_minus_a": round(diff, 4),
            "p_value": round(p_val, 5),
        }

    return {
        "ticks": ticks,
        "seeds": trial_seeds,
        "config_a": {"name": config_a.name, "scenario_id": config_a.scenario_id},
        "config_b": {"name": config_b.name, "scenario_id": config_b.scenario_id},
        "metrics": comparison,
    }


def compare_saved_histories(
    exp_a: dict[str, Any],
    hist_a: list[dict[str, Any]],
    exp_b: dict[str, Any],
    hist_b: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compare two already-executed experiments using their tail windows."""
    if not hist_a or not hist_b:
        return {"error": "Both experiments must have at least 1 recorded simulation tick."}

    win_a = hist_a[-min(10, len(hist_a)) :]
    win_b = hist_b[-min(10, len(hist_b)) :]
    metrics_out: dict[str, Any] = {}
    for m in COMPARE_METRICS:
        sa = summarize_samples([float(r[m]) for r in win_a])
        sb = summarize_samples([float(r[m]) for r in win_b])
        metrics_out[m] = {
            "experiment_a": sa,
            "experiment_b": sb,
            "mean_diff_b_minus_a": round(sb["mean"] - sa["mean"], 4),
        }

    return {
        "experiment_a": {"id": exp_a["id"], "name": exp_a["name"], "ticks": len(hist_a)},
        "experiment_b": {"id": exp_b["id"], "name": exp_b["name"], "ticks": len(hist_b)},
        "metrics": metrics_out,
        "series_a": hist_a,
        "series_b": hist_b,
    }
