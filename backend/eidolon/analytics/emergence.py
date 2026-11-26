"""Emergent Behaviour Detection Engine: strictly grounded in statistical & network measurements."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np

from eidolon.analytics.metrics import (
    compute_network_analytics,
    compute_spatial_entropy,
    compute_wealth_distribution,
)
from eidolon.social.culture import measure_cultural_metrics

if TYPE_CHECKING:
    from eidolon.core.engine import SimulationEngine


def detect_emergent_patterns(engine: SimulationEngine) -> list[dict[str, Any]]:
    """Analyze simulation history and current state to report measurable emergent phenomena.

    Every finding includes its exact measurement method, baseline vs current values,
    and supporting data—never speculative civilization claims.
    """
    hist = engine.metrics_history
    tick = engine.clock.tick
    if tick < 5 or len(hist) < 5:
        return [
            {
                "pattern_id": "insufficient_baseline",
                "category": "baseline",
                "title": "Collecting Baseline Observations",
                "measured_claim": f"Simulation at tick {tick}; minimum 5 ticks required for trend measurement.",
                "measurement_method": "Windowed time-series comparison",
                "baseline_value": 0.0,
                "current_value": float(tick),
                "delta": float(tick),
                "confidence_score": 1.0,
                "supporting_data": {"ticks_observed": tick},
            }
        ]

    patterns: list[dict[str, Any]] = []
    win = max(3, min(15, len(hist) // 4))
    early = hist[:win]
    recent = hist[-win:]

    def mean_field(rows: list[dict[str, Any]], key: str) -> float:
        return float(np.mean([r[key] for r in rows]))

    # 1. Cooperation trajectory
    coop_early = mean_field(early, "cooperation_index")
    coop_recent = mean_field(recent, "cooperation_index")
    coop_delta = coop_recent - coop_early
    patterns.append(
        {
            "pattern_id": "cooperation_trajectory",
            "category": "cooperation_clusters",
            "title": "Cooperation Rate Shift" if abs(coop_delta) >= 0.05 else "Stable Cooperation Regime",
            "measured_claim": (
                f"Measured cooperation frequency shifted from {coop_early * 100:.1f}% "
                f"(ticks 1–{win}) to {coop_recent * 100:.1f}% (last {win} ticks) over {tick} cycles."
            ),
            "measurement_method": "Early-vs-recent window mean of cooperative / total social interaction ratio",
            "baseline_value": round(coop_early, 4),
            "current_value": round(coop_recent, 4),
            "delta": round(coop_delta, 4),
            "confidence_score": round(min(0.99, 0.55 + abs(coop_delta) * 1.5), 3),
            "supporting_data": {
                "total_cooperations": engine.total_cooperations,
                "total_interactions": engine.total_interactions,
                "window_size": win,
            },
        }
    )

    # 2. Social network & community formation
    net_stats = compute_network_analytics(engine)
    comm_count = len(engine.network.communities)
    mean_cohesion = (
        float(np.mean([c.cohesion for c in engine.network.communities.values()]))
        if engine.network.communities
        else 0.0
    )
    patterns.append(
        {
            "pattern_id": "community_formation",
            "category": "social_network",
            "title": f"{comm_count} Emergent Social Clusters Detected" if comm_count > 0 else "Unclustered Social Graph",
            "measured_claim": (
                f"NetworkX greedy modularity identified {comm_count} communities (>=3 members) "
                f"with clustering coefficient {net_stats['clustering_coefficient']:.3f} and density {net_stats['density']:.4f}."
            ),
            "measurement_method": "NetworkX greedy modularity community detection + average clustering coefficient",
            "baseline_value": 0.0,
            "current_value": float(comm_count),
            "delta": float(comm_count),
            "confidence_score": round(min(0.98, 0.5 + 0.45 * net_stats["clustering_coefficient"]), 3),
            "supporting_data": {
                "community_count": comm_count,
                "mean_cohesion": round(mean_cohesion, 4),
                "clustering_coefficient": net_stats["clustering_coefficient"],
                "network_density": net_stats["density"],
                "active_edges": net_stats["edges"],
            },
        }
    )

    # 3. Resource inequality (Gini)
    gini_early = mean_field(early, "gini_coefficient")
    gini_recent = mean_field(recent, "gini_coefficient")
    wealth_dist = compute_wealth_distribution(engine)
    patterns.append(
        {
            "pattern_id": "resource_inequality",
            "category": "inequality",
            "title": "Wealth Stratification" if gini_recent > 0.25 else "Relatively Egalitarian Wealth Distribution",
            "measured_claim": (
                f"Gini coefficient moved from {gini_early:.3f} to {gini_recent:.3f}; "
                f"top 10% of agents hold {wealth_dist['top_10_share'] * 100:.1f}% of total inventory value."
            ),
            "measurement_method": "Exact Gini coefficient over price-weighted agent resource inventories",
            "baseline_value": round(gini_early, 4),
            "current_value": round(gini_recent, 4),
            "delta": round(gini_recent - gini_early, 4),
            "confidence_score": 0.95,
            "supporting_data": wealth_dist,
        }
    )

    # 4. Cultural convergence & divergence
    alive = [ag for ag in engine.agents.values() if ag.alive]
    cult = measure_cultural_metrics(alive, engine.network.communities)
    div_early = mean_field(early, "cultural_diversity")
    div_recent = cult["cultural_diversity"]
    patterns.append(
        {
            "pattern_id": "cultural_dynamics",
            "category": "cultural_divergence",
            "title": "Cultural Convergence" if div_recent < div_early - 0.04 else "Cultural Pluralism / Divergence",
            "measured_claim": (
                f"Normalized cultural Shannon entropy moved from {div_early:.3f} to {div_recent:.3f}; "
                f"generous-sharing norm adoption is {cult['sharing_norm_adoption'] * 100:.1f}% "
                f"with inter-community L1 divergence {cult['inter_community_divergence']:.3f}."
            ),
            "measurement_method": "Normalized Shannon entropy across 4 cultural traits + pairwise community L1 distance",
            "baseline_value": round(div_early, 4),
            "current_value": round(div_recent, 4),
            "delta": round(div_recent - div_early, 4),
            "confidence_score": 0.92,
            "supporting_data": cult,
        }
    )

    # 5. Group polarization / Trust variance
    all_edges = list(engine.network.edges.values())
    rivalry_edges = [e for e in all_edges if e.rel_type == "rivalry"]
    trusts = [e.trust for e in all_edges]
    trust_std = float(np.std(trusts)) if trusts else 0.0
    rivalry_ratio = len(rivalry_edges) / max(1, len(all_edges))
    patterns.append(
        {
            "pattern_id": "trust_polarisation",
            "category": "polarisation",
            "title": "Trust Polarisation Detected" if trust_std > 0.22 or rivalry_ratio > 0.25 else "Cohesive Trust Profile",
            "measured_claim": (
                f"Mean relationship trust is {engine.network.mean_trust():.3f} (std {trust_std:.3f}); "
                f"rivalry edges represent {rivalry_ratio * 100:.1f}% of {len(all_edges)} tracked ties."
            ),
            "measurement_method": "Trust standard deviation & rivalry-edge fraction across relationship graph",
            "baseline_value": 0.5,
            "current_value": round(engine.network.mean_trust(), 4),
            "delta": round(engine.network.mean_trust() - 0.5, 4),
            "confidence_score": 0.90,
            "supporting_data": {
                "trust_std": round(trust_std, 4),
                "rivalry_edges": len(rivalry_edges),
                "total_edges": len(all_edges),
                "rivalry_ratio": round(rivalry_ratio, 4),
            },
        }
    )

    # 6. Institutional development
    active_insts = engine.institutions.active_list()
    covered = sum(i["member_count"] for i in active_insts)
    coverage_rate = covered / max(1, len(alive))
    patterns.append(
        {
            "pattern_id": "institutional_development",
            "category": "institutions",
            "title": f"{len(active_insts)} Active Institutions" if active_insts else "Pre-Institutional Society",
            "measured_claim": (
                f"{len(active_insts)} active institutions cover {coverage_rate * 100:.1f}% of population "
                f"with mean stability {engine.institutions.mean_stability():.3f}."
            ),
            "measurement_method": "Active institutional membership coverage and stability index",
            "baseline_value": 0.0,
            "current_value": float(len(active_insts)),
            "delta": float(len(active_insts)),
            "confidence_score": 0.96,
            "supporting_data": {
                "active_institutions": len(active_insts),
                "population_coverage": round(coverage_rate, 4),
                "mean_stability": round(engine.institutions.mean_stability(), 4),
            },
        }
    )

    # 7. Spatial concentration & migration
    spatial_h = compute_spatial_entropy(engine)
    patterns.append(
        {
            "pattern_id": "population_migration",
            "category": "migration",
            "title": "Spatial Clustering" if spatial_h < 0.85 else "Dispersed Population Distribution",
            "measured_claim": (
                f"Spatial location entropy is {spatial_h:.3f} (1.0 = uniform across {len(engine.world.locations)} nodes)."
            ),
            "measurement_method": "Normalized Shannon entropy of agent headcounts across world graph locations",
            "baseline_value": 1.0,
            "current_value": spatial_h,
            "delta": round(spatial_h - 1.0, 4),
            "confidence_score": 0.94,
            "supporting_data": {"spatial_entropy": spatial_h, "locations": len(engine.world.locations)},
        }
    )

    # 8. Learning & Collective Intelligence
    q_early = mean_field(early, "mean_q_value")
    q_recent = mean_field(recent, "mean_q_value")
    total_social_adoptions = sum(ag.q_learner.social_adoptions for ag in alive)
    patterns.append(
        {
            "pattern_id": "learning_convergence",
            "category": "collective_intelligence",
            "title": "Reinforcement & Social Learning Progression",
            "measured_claim": (
                f"Mean Q-value shifted from {q_early:.3f} to {q_recent:.3f}; "
                f"{total_social_adoptions} cross-agent strategy adoptions and "
                f"{engine.collective_successes}/{max(1, engine.collective_attempts)} collective successes recorded."
            ),
            "measurement_method": "Population mean Q-table update trajectory + social learning adoption counter",
            "baseline_value": round(q_early, 4),
            "current_value": round(q_recent, 4),
            "delta": round(q_recent - q_early, 4),
            "confidence_score": 0.93,
            "supporting_data": {
                "social_adoptions": total_social_adoptions,
                "collective_success_rate": round(engine.collective_successes / max(1, engine.collective_attempts), 4),
            },
        }
    )

    engine.detected_patterns = patterns
    return patterns
