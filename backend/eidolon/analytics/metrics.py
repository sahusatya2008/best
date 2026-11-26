"""Network science, inequality, and behavioral analytics computed from actual simulation state."""

from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING, Any

import networkx as nx
import numpy as np

if TYPE_CHECKING:
    from eidolon.core.engine import SimulationEngine


def compute_network_analytics(engine: SimulationEngine) -> dict[str, Any]:
    """Compute NetworkX centrality, clustering coefficient, and community statistics."""
    alive_ids = [aid for aid, ag in engine.agents.items() if ag.alive]
    g = engine.network.to_networkx(alive_ids, min_interactions=1)
    n = g.number_of_nodes()
    m = g.number_of_edges()

    if n == 0 or m == 0:
        return {
            "nodes": n,
            "edges": m,
            "density": 0.0,
            "clustering_coefficient": 0.0,
            "mean_degree": 0.0,
            "top_degree_centrality": [],
            "top_betweenness_centrality": [],
            "communities": [c.to_dict() for c in engine.network.communities.values()],
        }

    density = float(nx.density(g))
    clustering = float(nx.average_clustering(g))
    degrees = dict(g.degree())
    mean_deg = sum(degrees.values()) / max(1, n)

    deg_cent = nx.degree_centrality(g)
    # Use exact betweenness for <=400 nodes, k-sampled approximation for larger graphs to stay responsive on M1
    k_sample = min(n, 80) if n > 400 else None
    bet_cent = nx.betweenness_centrality(g, k=k_sample, seed=engine.config.seed)

    top_deg = sorted(deg_cent.items(), key=lambda kv: kv[1], reverse=True)[:10]
    top_bet = sorted(bet_cent.items(), key=lambda kv: kv[1], reverse=True)[:10]

    return {
        "nodes": n,
        "edges": m,
        "density": round(density, 5),
        "clustering_coefficient": round(clustering, 4),
        "mean_degree": round(mean_deg, 3),
        "top_degree_centrality": [
            {"agent_id": aid, "name": engine.agents[aid].name, "value": round(val, 4)}
            for aid, val in top_deg
        ],
        "top_betweenness_centrality": [
            {"agent_id": aid, "name": engine.agents[aid].name, "value": round(val, 4)}
            for aid, val in top_bet
        ],
        "communities": [c.to_dict() for c in engine.network.communities.values()],
    }


def compute_wealth_distribution(engine: SimulationEngine) -> dict[str, Any]:
    """Compute Gini, top-10% share, bottom-50% share, and wealth quantiles."""
    prices = engine.economy.prices
    wealths = np.array(
        [ag.wealth(prices) for ag in engine.agents.values() if ag.alive],
        dtype=np.float64,
    )
    if len(wealths) == 0:
        return {"gini": 0.0, "top_10_share": 0.0, "bottom_50_share": 0.0, "mean_wealth": 0.0, "median_wealth": 0.0}

    sorted_w = np.sort(wealths)
    total = float(np.sum(sorted_w)) or 1e-9
    k10 = max(1, int(0.1 * len(sorted_w)))
    k50 = max(1, int(0.5 * len(sorted_w)))
    top10 = float(np.sum(sorted_w[-k10:])) / total
    bot50 = float(np.sum(sorted_w[:k50])) / total
    gini = engine.economy.compute_gini([ag.resources for ag in engine.agents.values() if ag.alive])

    return {
        "gini": round(gini, 4),
        "top_10_share": round(top10, 4),
        "bottom_50_share": round(bot50, 4),
        "mean_wealth": round(float(np.mean(wealths)), 3),
        "median_wealth": round(float(np.median(wealths)), 3),
    }


def compute_spatial_entropy(engine: SimulationEngine) -> float:
    """Normalized Shannon entropy of agent population across world locations (0=concentrated, 1=uniform)."""
    alive = [ag for ag in engine.agents.values() if ag.alive]
    n_locs = len(engine.world.locations)
    if not alive or n_locs <= 1:
        return 0.0
    counts = Counter(ag.location_id for ag in alive)
    probs = np.array([counts.get(lid, 0) / len(alive) for lid in engine.world.locations], dtype=np.float64)
    nz = probs[probs > 0]
    h = float(-np.sum(nz * np.log2(nz)))
    return round(h / float(np.log2(n_locs)), 4)
