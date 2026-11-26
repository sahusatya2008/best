"""Utility-based decision engine with full mathematical breakdown and explainability."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from eidolon.agent.learning import ACTIONS, LearningConfig
from eidolon.core.rng import SeededRNG

if TYPE_CHECKING:
    from eidolon.agent.cognition import Agent
    from eidolon.agent.memory import MemoryEntry


@dataclass
class ActionEvaluation:
    """Detailed breakdown of why an action received its utility score."""

    action: str
    need_satisfaction: float
    expected_reward: float
    action_cost: float
    risk: float
    personality_bias: float
    social_consequence: float
    resource_availability: float
    past_experience: float
    goal_relevance: float
    uncertainty: float
    total_utility: float
    feasible: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "need_satisfaction": round(self.need_satisfaction, 4),
            "expected_reward": round(self.expected_reward, 4),
            "action_cost": round(self.action_cost, 4),
            "risk": round(self.risk, 4),
            "personality_bias": round(self.personality_bias, 4),
            "social_consequence": round(self.social_consequence, 4),
            "resource_availability": round(self.resource_availability, 4),
            "past_experience": round(self.past_experience, 4),
            "goal_relevance": round(self.goal_relevance, 4),
            "uncertainty": round(self.uncertainty, 4),
            "total_utility": round(self.total_utility, 4),
            "feasible": self.feasible,
        }


def calculate_action_utility(
    action: str,
    agent: Agent,
    environment: dict[str, Any],
    memory_context: dict[str, Any],
) -> ActionEvaluation:
    """Computes grounded multi-factor utility for a candidate action."""
    needs = agent.needs
    traits = agent.traits
    inv = agent.resources
    local_stocks: dict[str, float] = environment.get("local_stocks", {})
    nearby_count: int = int(environment.get("nearby_count", 0))
    best_partner_trust: float = float(environment.get("best_partner_trust", 0.5))
    hazard: float = float(environment.get("hazard_level", 0.05))
    coop_bonus_cfg: float = float(environment.get("cooperation_reward", 0.25))
    scarcity_lvl: float = float(environment.get("scarcity", 0.3))
    in_institution: bool = bool(environment.get("in_institution", False))
    state_key: str = str(environment.get("state_key", "default"))

    # 1. Need satisfaction potential (0..1)
    need_sat = 0.05
    if action == "harvest_food":
        need_sat = (1.0 - needs.nutrition) * 0.95 + (1.0 - needs.resource_security) * 0.35
    elif action == "gather_water":
        need_sat = (1.0 - needs.nutrition) * 0.65 + (1.0 - needs.safety) * 0.20 + (1.0 - needs.resource_security) * 0.30
    elif action == "extract_materials":
        need_sat = (1.0 - needs.resource_security) * 0.60 + (1.0 - needs.achievement) * 0.30
    elif action == "craft_tools":
        need_sat = (1.0 - needs.achievement) * 0.65 + (1.0 - needs.resource_security) * 0.45
    elif action == "research_knowledge":
        need_sat = (1.0 - needs.knowledge_acquisition) * 0.95 + (1.0 - needs.achievement) * 0.25
    elif action == "cooperate":
        need_sat = (1.0 - needs.social_connection) * 0.55 + (1.0 - needs.belonging) * 0.65
    elif action == "trade":
        need_sat = (1.0 - needs.resource_security) * 0.55 + (1.0 - needs.nutrition) * 0.35 + (1.0 - needs.social_connection) * 0.20
    elif action == "compete":
        need_sat = (1.0 - needs.resource_security) * 0.50 + (1.0 - needs.achievement) * 0.35
    elif action == "communicate":
        need_sat = (1.0 - needs.social_connection) * 0.80 + (1.0 - needs.belonging) * 0.40
    elif action == "migrate":
        need_sat = (1.0 - needs.safety) * 0.55 + scarcity_lvl * 0.50
    elif action == "rest":
        need_sat = (1.0 - needs.energy) * 1.05 + (1.0 - needs.safety) * 0.25
    need_sat = min(1.2, max(0.0, need_sat))

    # 2. Expected reward from Q-learning + procedural memory
    q_val = agent.q_learner.get_q(state_key, action)
    proc = agent.memory.procedural.get(action)
    proc_expect = proc.avg_outcome if proc else 0.0
    expected_reward = max(-0.8, min(1.0, 0.55 * q_val + 0.45 * proc_expect))

    # 3. Action cost (energy & input consumption)
    cost_map = {
        "harvest_food": 0.16,
        "gather_water": 0.14,
        "extract_materials": 0.22,
        "craft_tools": 0.26,
        "research_knowledge": 0.18,
        "cooperate": 0.14,
        "trade": 0.12,
        "compete": 0.28,
        "communicate": 0.08,
        "migrate": 0.25,
        "rest": 0.02,
    }
    action_cost = cost_map.get(action, 0.15)
    if needs.energy < 0.25 and action != "rest":
        action_cost += 0.25

    # 4. Risk (environmental hazard + failure history + social retaliation)
    fail_pen = agent.q_learner.failure_penalty(action)
    risk = hazard * 0.5 + fail_pen
    if action == "compete":
        risk += 0.22 + (0.15 if in_institution else 0.0)
    elif action == "migrate":
        risk += 0.12 + (1.0 - traits.emotional_stability) * 0.15
    risk = min(1.0, max(0.0, risk))

    # 5. Big Five Personality mathematical weights
    if action == "cooperate":
        p_bias = 0.35 * traits.agreeableness + 0.18 * traits.extraversion + 0.10 * traits.conscientiousness
    elif action == "communicate":
        p_bias = 0.40 * traits.extraversion + 0.18 * traits.agreeableness + 0.10 * traits.openness
    elif action == "trade":
        p_bias = 0.22 * traits.conscientiousness + 0.20 * traits.extraversion + 0.10 * traits.agreeableness
    elif action == "compete":
        p_bias = 0.35 * (1.0 - traits.agreeableness) + 0.18 * (1.0 - traits.emotional_stability)
    elif action == "research_knowledge":
        p_bias = 0.42 * traits.openness + 0.18 * traits.conscientiousness
    elif action == "migrate":
        p_bias = 0.38 * traits.openness + 0.12 * (1.0 - traits.emotional_stability)
    elif action == "craft_tools":
        p_bias = 0.35 * traits.conscientiousness + 0.12 * traits.openness
    elif action == "rest":
        p_bias = 0.22 * (1.0 - traits.extraversion) + 0.10 * traits.emotional_stability
    else:
        p_bias = 0.20 * traits.conscientiousness

    # Cultural trait alignment modifier
    sharing_norm = agent.cultural_traits.get("sharing_norm", "balanced")
    if action == "cooperate" and sharing_norm == "generous":
        p_bias += 0.14
    elif action == "compete" and sharing_norm == "hoarding":
        p_bias += 0.10

    # 6. Social consequence (trust, reputation, institutional norms)
    social_conseq = 0.0
    if action == "cooperate":
        social_conseq = 0.35 * best_partner_trust + 0.30 * coop_bonus_cfg + (0.15 if in_institution else 0.0)
    elif action == "trade":
        social_conseq = 0.28 * best_partner_trust + 0.15
    elif action == "communicate":
        social_conseq = 0.25 * best_partner_trust + 0.12
    elif action == "compete":
        social_conseq = -0.25 * best_partner_trust - (0.20 if in_institution else 0.0)
    elif action == "research_knowledge":
        social_conseq = 0.12 * agent.reputation

    # 7. Resource / Partner availability (feasibility)
    feasible = True
    res_avail = 0.7
    if action == "harvest_food":
        q = local_stocks.get("food", 0.0)
        res_avail = min(1.0, q / 25.0)
        feasible = q >= 0.4
    elif action == "gather_water":
        q = local_stocks.get("water", 0.0)
        res_avail = min(1.0, q / 25.0)
        feasible = q >= 0.4
    elif action == "extract_materials":
        q = local_stocks.get("raw_materials", 0.0) + local_stocks.get("energy", 0.0)
        res_avail = min(1.0, q / 35.0)
        feasible = q >= 0.4
    elif action == "craft_tools":
        has_mats = inv.get("raw_materials", 0.0) >= 1.0 and inv.get("energy", 0.0) >= 0.5
        res_avail = 0.85 if has_mats else 0.05
        feasible = has_mats
    elif action in ("cooperate", "trade", "compete", "communicate"):
        feasible = nearby_count > 0
        res_avail = min(1.0, nearby_count / 4.0) if feasible else 0.0
        if action == "trade":
            has_surplus = any(inv.get(r, 0.0) >= 0.8 for r in inv)
            feasible = feasible and has_surplus
    elif action == "research_knowledge":
        res_avail = 0.85 if environment.get("location_kind") in ("sanctuary", "settlement") else 0.55
    elif action == "migrate":
        feasible = len(environment.get("neighbors", [])) > 0
        res_avail = 0.7 if feasible else 0.0

    # 8. Past experience from retrieved episodic memories
    similar_memories: list[tuple[float, MemoryEntry]] = memory_context.get("by_action", {}).get(action, [])
    if similar_memories:
        w_sum = sum(s for s, _ in similar_memories) or 1.0
        past_exp = sum(s * m.outcome for s, m in similar_memories) / w_sum
        past_exp = max(-0.6, min(0.8, past_exp))
    else:
        past_exp = 0.0

    # 9. Goal relevance
    goal_rel = 0.0
    for g in agent.goals:
        if not g.active:
            continue
        if g.goal_type == "survive" and action in ("harvest_food", "gather_water", "rest"):
            goal_rel += 0.35 * g.priority
        elif g.goal_type == "prosper" and action in ("trade", "craft_tools", "extract_materials"):
            goal_rel += 0.32 * g.priority
        elif g.goal_type in ("belong", "cooperate") and action in ("cooperate", "communicate"):
            goal_rel += 0.36 * g.priority
        elif g.goal_type == "learn" and action in ("research_knowledge", "communicate"):
            goal_rel += 0.36 * g.priority
        elif g.goal_type == "explore" and action in ("migrate", "research_knowledge"):
            goal_rel += 0.32 * g.priority
        elif g.goal_type == "lead" and action in ("cooperate", "compete", "communicate"):
            goal_rel += 0.25 * g.priority
    goal_rel = min(0.8, goal_rel)

    # 10. Uncertainty / exploration bonus
    visits = proc.successes + proc.failures if proc else 0
    uncertainty = (1.0 / (1.0 + 0.25 * visits)) * (0.35 + 0.65 * traits.openness)

    if not feasible:
        total = -1.0
    else:
        total = (
            0.34 * need_sat
            + 0.22 * expected_reward
            + 0.14 * p_bias
            + 0.14 * social_conseq
            + 0.12 * res_avail
            + 0.10 * past_exp
            + 0.12 * goal_rel
            + 0.06 * uncertainty
            - 0.18 * action_cost
            - 0.16 * risk
        )

    return ActionEvaluation(
        action=action,
        need_satisfaction=need_sat,
        expected_reward=expected_reward,
        action_cost=action_cost,
        risk=risk,
        personality_bias=p_bias,
        social_consequence=social_conseq,
        resource_availability=res_avail,
        past_experience=past_exp,
        goal_relevance=goal_rel,
        uncertainty=uncertainty,
        total_utility=total,
        feasible=feasible,
    )


def select_action_with_explanation(
    agent: Agent,
    environment: dict[str, Any],
    memory_context: dict[str, Any],
    learn_cfg: LearningConfig,
    rng: SeededRNG,
    tick: int,
) -> tuple[str, dict[str, Any]]:
    """Evaluates all actions, selects via epsilon-greedy / utility weighting, and returns full explanation."""
    evals: list[ActionEvaluation] = [
        calculate_action_utility(act, agent, environment, memory_context)
        for act in ACTIONS
    ]
    feasible = [e for e in evals if e.feasible]
    if not feasible:
        feasible = [next(e for e in evals if e.action == "rest")]

    feasible.sort(key=lambda e: e.total_utility, reverse=True)

    # Configurable stochastic exploration vs utility-weighted selection
    eps = max(0.0, min(0.8, learn_cfg.exploration_rate * (0.6 + 0.6 * agent.traits.openness)))
    if rng.random() < eps and len(feasible) > 1:
        chosen = rng.choice(feasible[: min(4, len(feasible))])
        mechanism = "Epsilon-guided stochastic exploration"
    else:
        # Softmax over top utilities for bounded non-determinism
        top_n = feasible[: min(3, len(feasible))]
        max_u = top_n[0].total_utility
        temp = 0.08 + 0.06 * (1.0 - agent.traits.conscientiousness)
        import math

        weights = [math.exp(max(-10.0, min(10.0, (e.total_utility - max_u) / max(0.02, temp)))) for e in top_n]
        chosen = rng.choices(top_n, weights=weights, k=1)[0]
        mechanism = "Weighted utility selection"

    alternatives = [
        {"action": e.action, "utility": round(e.total_utility, 4)}
        for e in feasible
        if e.action != chosen.action
    ][:3]

    explanation = {
        "tick": tick,
        "selected_action": chosen.action,
        "selected_utility": round(chosen.total_utility, 4),
        "decision_mechanism": mechanism,
        "decision_factors": {
            "need_satisfaction": round(chosen.need_satisfaction, 4),
            "expected_reward": round(chosen.expected_reward, 4),
            "resource_cost": round(chosen.action_cost, 4),
            "risk": round(chosen.risk, 4),
            "personality_bias": round(chosen.personality_bias, 4),
            "social_benefit": round(chosen.social_consequence, 4),
            "resource_availability": round(chosen.resource_availability, 4),
            "past_experience": round(chosen.past_experience, 4),
            "goal_relevance": round(chosen.goal_relevance, 4),
            "uncertainty": round(chosen.uncertainty, 4),
        },
        "alternatives": alternatives,
        "state_key": environment.get("state_key", "default"),
        "most_urgent_need": agent.needs.most_urgent()[0],
    }
    return chosen.action, explanation
