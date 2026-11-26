"""Cultural transmission, social norm measurement, and inter-community cultural divergence."""

from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING, Any

import numpy as np

from eidolon.core.rng import SeededRNG

if TYPE_CHECKING:
    from eidolon.agent.cognition import Agent
    from eidolon.social.relationships import Community


CULTURAL_TRAIT_OPTIONS: dict[str, tuple[str, ...]] = {
    "sharing_norm": ("generous", "balanced", "hoarding"),
    "work_ethic": ("industrious", "collaborative", "exploratory"),
    "conflict_style": ("diplomatic", "assertive", "avoidant"),
    "governance_pref": ("council", "market", "autonomous"),
}


def attempt_cultural_transmission(
    sender: Agent,
    receiver: Agent,
    trust: float,
    transmission_rate: float,
    rng: SeededRNG,
) -> tuple[str, str] | None:
    """Transmit a cultural trait if trust and perceived payoff/affinity support adoption."""
    payoff_diff = sender.last_reward - receiver.last_reward
    payoff_factor = 1.0 if payoff_diff > 0.02 else 0.55
    same_comm = 1.25 if (sender.community_id and sender.community_id == receiver.community_id) else 1.0
    prob = min(0.85, transmission_rate * (0.35 + 0.65 * trust) * payoff_factor * same_comm)
    if rng.random() > prob:
        return None

    trait_name = rng.choice(list(CULTURAL_TRAIT_OPTIONS.keys()))
    sender_val = sender.cultural_traits.get(trait_name)
    if not sender_val or sender_val == receiver.cultural_traits.get(trait_name):
        return None

    receiver.cultural_traits[trait_name] = sender_val
    return trait_name, sender_val


def measure_cultural_metrics(
    agents: list[Agent],
    communities: dict[str, Community],
) -> dict[str, Any]:
    """Compute normalized cultural entropy (diversity), norm adoption rates, and inter-community divergence."""
    if not agents:
        return {
            "cultural_diversity": 0.0,
            "sharing_norm_adoption": 0.0,
            "collaborative_ethic_rate": 0.0,
            "inter_community_divergence": 0.0,
            "trait_distributions": {},
        }

    distributions: dict[str, dict[str, float]] = {}
    entropies: list[float] = []
    n = len(agents)

    for trait, options in CULTURAL_TRAIT_OPTIONS.items():
        counts = Counter(ag.cultural_traits.get(trait, options[0]) for ag in agents)
        probs = np.array([counts.get(opt, 0) / n for opt in options], dtype=np.float64)
        distributions[trait] = {opt: round(float(p), 4) for opt, p in zip(options, probs)}
        nz = probs[probs > 0]
        h = float(-np.sum(nz * np.log2(nz))) if len(nz) > 0 else 0.0
        max_h = float(np.log2(len(options)))
        entropies.append(h / max_h if max_h > 0 else 0.0)

    cultural_diversity = sum(entropies) / len(entropies)
    generous_rate = distributions["sharing_norm"].get("generous", 0.0)
    collab_rate = distributions["work_ethic"].get("collaborative", 0.0)

    # Inter-community cultural divergence (mean L1 distance between community trait vectors)
    divergence = 0.0
    if len(communities) >= 2:
        by_id = {ag.agent_id: ag for ag in agents}
        comm_vecs: list[np.ndarray] = []
        for comm in communities.values():
            members = [by_id[mid] for mid in comm.member_ids if mid in by_id]
            if not members:
                continue
            vec = []
            for trait, options in CULTURAL_TRAIT_OPTIONS.items():
                counts = Counter(m.cultural_traits.get(trait, options[0]) for m in members)
                for opt in options:
                    vec.append(counts.get(opt, 0) / len(members))
            comm_vecs.append(np.array(vec, dtype=np.float64))
        if len(comm_vecs) >= 2:
            dists = []
            for i in range(len(comm_vecs)):
                for j in range(i + 1, len(comm_vecs)):
                    dists.append(float(np.mean(np.abs(comm_vecs[i] - comm_vecs[j]))))
            divergence = sum(dists) / len(dists)

    return {
        "cultural_diversity": round(cultural_diversity, 4),
        "sharing_norm_adoption": round(generous_rate, 4),
        "collaborative_ethic_rate": round(collab_rate, 4),
        "inter_community_divergence": round(divergence, 4),
        "trait_distributions": distributions,
    }
