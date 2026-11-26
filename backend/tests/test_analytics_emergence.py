"""Tests for emergent pattern detection, controlled experiment comparisons, and scientific reports."""

from pathlib import Path

from eidolon.analytics.comparison import run_controlled_comparison
from eidolon.analytics.emergence import detect_emergent_patterns
from eidolon.analytics.reports import export_experiment_bundle
from eidolon.core.engine import ExperimentConfig, SimulationEngine


def test_emergence_detection_and_controlled_experiment_comparison():
    cfg_low = ExperimentConfig(
        name="No Coop Synergy",
        population_size=30,
        cooperation_reward=0.0,
        scarcity=0.55,
        seed=42,
        duration_ticks=40,
    )
    cfg_high = ExperimentConfig(
        name="High Coop Synergy",
        population_size=30,
        cooperation_reward=0.55,
        scarcity=0.15,
        seed=42,
        duration_ticks=40,
    )
    cmp_res = run_controlled_comparison(cfg_low, cfg_high, seeds=[11, 22], ticks=35)
    assert "cooperation_index" in cmp_res["metrics"]
    coop_cmp = cmp_res["metrics"]["cooperation_index"]
    assert coop_cmp["experiment_b"]["mean"] >= coop_cmp["experiment_a"]["mean"]
    assert "ci95_low" in coop_cmp["experiment_a"]

    eng = SimulationEngine("emg_test", cfg_high)
    for _ in range(30):
        eng.step()
    patterns = detect_emergent_patterns(eng)
    assert len(patterns) >= 6
    for p in patterns:
        assert "measurement_method" in p
        assert "supporting_data" in p

    exported = export_experiment_bundle(eng)
    assert Path(exported["json_path"]).exists()
    assert Path(exported["csv_path"]).exists()
    assert Path(exported["chart_path"]).exists()
