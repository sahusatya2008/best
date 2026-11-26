"""Scientific report generation (Matplotlib figures + structured JSON/CSV exports)."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from eidolon.analytics.emergence import detect_emergent_patterns
from eidolon.config import EXPORTS_DIR, REPORTS_DIR

if TYPE_CHECKING:
    from eidolon.core.engine import SimulationEngine


def export_experiment_bundle(engine: SimulationEngine) -> dict[str, str]:
    """Export complete experiment configuration, metrics CSV, JSON bundle, and Matplotlib chart."""
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    eid = engine.experiment_id
    tick = engine.clock.tick

    # 1. Complete JSON bundle
    json_path = EXPORTS_DIR / f"eidolon_{eid}_tick{tick}.json"
    patterns = detect_emergent_patterns(engine)
    bundle = {
        "summary": engine.state_summary(),
        "emergent_patterns": patterns,
        "metrics_history": engine.metrics_history,
        "institutions": engine.institutions.active_list(),
        "communities": [c.to_dict() for c in engine.network.communities.values()],
        "recent_events": engine.events.recent_list(limit=250),
    }
    json_path.write_text(json.dumps(bundle, indent=2), encoding="utf-8")

    # 2. Metrics CSV
    csv_path = EXPORTS_DIR / f"eidolon_{eid}_metrics.csv"
    if engine.metrics_history:
        fieldnames = list(engine.metrics_history[0].keys())
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(engine.metrics_history)
    else:
        csv_path.write_text("", encoding="utf-8")

    # 3. Matplotlib scientific multi-panel PNG report
    chart_path = REPORTS_DIR / f"eidolon_{eid}_report.png"
    _render_matplotlib_report(engine, chart_path)

    return {
        "json_path": str(json_path),
        "csv_path": str(csv_path),
        "chart_path": str(chart_path),
    }


def _render_matplotlib_report(engine: SimulationEngine, out_path: Path) -> None:
    hist = engine.metrics_history
    fig, axes = plt.subplots(2, 2, figsize=(12, 8), facecolor="#0b0d10")
    fig.suptitle(
        f"EIDOLON Scientific Report — {engine.config.name} (Seed {engine.config.seed}, Tick {engine.clock.tick})",
        color="#e2e8f0",
        fontsize=13,
        fontweight="bold",
    )

    ticks = [r["tick"] for r in hist] if hist else [0]
    series_cfg = [
        (axes[0, 0], [("cooperation_index", "#34d399", "Cooperation"), ("mean_trust", "#38bdf8", "Mean Trust")], "Cooperation & Trust"),
        (axes[0, 1], [("gini_coefficient", "#fb7185", "Gini Inequality"), ("cultural_diversity", "#a78bfa", "Cultural Diversity")], "Inequality & Culture"),
        (axes[1, 0], [("avg_need_satisfaction", "#fbbf24", "Need Satisfaction"), ("collective_success_rate", "#34d399", "Collective Success")], "Needs & Collective Quality"),
        (axes[1, 1], [("mean_q_value", "#38bdf8", "Mean Q-Value"), ("network_density", "#a78bfa", "Network Density")], "Learning & Network Density"),
    ]

    for ax, lines, title in series_cfg:
        ax.set_facecolor("#111419")
        ax.set_title(title, color="#cbd5e1", fontsize=10)
        ax.grid(True, color="#232a35", linestyle="--", linewidth=0.6)
        ax.tick_params(colors="#94a3b8", labelsize=8)
        for spine in ax.spines.values():
            spine.set_color("#232a35")
        if hist:
            for key, color, label in lines:
                ax.plot(ticks, [r[key] for r in hist], color=color, linewidth=1.8, label=label)
            ax.legend(facecolor="#161b22", edgecolor="#232a35", labelcolor="#e2e8f0", fontsize=8)

    plt.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(out_path, dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)
