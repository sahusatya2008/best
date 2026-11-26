"""Full Agent Cognitive Architecture (ACA) class and state serialization."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Any

from eidolon.agent.learning import LearningConfig, QLearningEngine
from eidolon.agent.memory import AgentMemory, MemoryEntry
from eidolon.agent.models import (
    DEFAULT_CULTURAL_TRAITS,
    OCCUPATIONS,
    AgentBelief,
    AgentGoal,
    AgentNeeds,
    BigFiveTraits,
    generate_agent_name,
)
from eidolon.agent.reasoning import select_action_with_explanation
from eidolon.core.rng import SeededRNG
from eidolon.world.economy import EconomicLedger
from eidolon.world.resources import RESOURCE_TYPES, empty_inventory, inventory_wealth


@dataclass
class Agent:
    """Autonomous computational individual with identity, needs, goals, beliefs, memory, and learning."""

    agent_id: str
    name: str
    birth_tick: int
    age: int
    generation: int
    occupation: str
    social_status: float
    location_id: str
    home_location_id: str
    community_id: str | None = None
    alive: bool = True

    traits: BigFiveTraits = field(default_factory=BigFiveTraits)
    needs: AgentNeeds = field(default_factory=AgentNeeds)
    resources: dict[str, float] = field(default_factory=empty_inventory)
    goals: list[AgentGoal] = field(default_factory=list)
    beliefs: dict[str, AgentBelief] = field(default_factory=dict)
    preferences: dict[str, float] = field(default_factory=dict)
    cultural_traits: dict[str, str] = field(default_factory=lambda: dict(DEFAULT_CULTURAL_TRAITS))

    memory: AgentMemory = field(default_factory=AgentMemory)
    q_learner: QLearningEngine = field(default_factory=QLearningEngine)

    reputation: float = 0.5
    last_action: str = "rest"
    last_reward: float = 0.0
    cumulative_reward: float = 0.0
    last_explanation: dict[str, Any] = field(default_factory=dict)
    decision_history: deque[dict[str, Any]] = field(default_factory=lambda: deque(maxlen=40))

    # Runtime per-tick scratch fields
    pending_state_key: str = "default"
    pending_pre_satisfaction: float = 0.6

    def compute_state_key(self, local_scarcity: float, nearby_count: int) -> str:
        urgent_need, _ = self.needs.most_urgent()
        scarcity_band = "high" if local_scarcity > 0.65 else ("med" if local_scarcity > 0.35 else "low")
        social_band = "crowded" if nearby_count >= 5 else ("social" if nearby_count >= 1 else "alone")
        energy_band = "tired" if self.needs.energy < 0.35 else "rested"
        return f"{urgent_need}|{scarcity_band}|{social_band}|{energy_band}"

    def perceive(
        self,
        local_stocks: dict[str, float],
        local_max: dict[str, float],
        hazard_level: float,
        location_kind: str,
        neighbors: list[str],
        nearby_agents: list[Agent],
        best_partner_trust: float,
        cooperation_reward: float,
        in_institution: bool,
    ) -> dict[str, Any]:
        """Step 1-2 of decision cycle: read internal state and observe environment."""
        total_cap = sum(local_max.values()) or 1.0
        total_qty = sum(local_stocks.values())
        scarcity = max(0.0, min(1.0, 1.0 - (total_qty / total_cap)))
        state_key = self.compute_state_key(scarcity, len(nearby_agents))
        self.pending_state_key = state_key
        self.pending_pre_satisfaction = self.needs.mean_satisfaction()

        return {
            "location_id": self.location_id,
            "location_kind": location_kind,
            "local_stocks": local_stocks,
            "hazard_level": hazard_level,
            "neighbors": neighbors,
            "nearby_count": len(nearby_agents),
            "best_partner_trust": best_partner_trust,
            "cooperation_reward": cooperation_reward,
            "scarcity": scarcity,
            "in_institution": in_institution,
            "state_key": state_key,
        }

    def retrieve_memory_context(self, observation: dict[str, Any], tick: int) -> dict[str, Any]:
        """Step 3: similarity-based retrieval from episodic memory."""
        _, urg = self.needs.most_urgent()
        query_ctx: dict[str, float | str] = {
            "location_id": self.location_id,
            "need_urgency": urg,
            "scarcity": observation["scarcity"],
            "social_density": min(1.0, observation["nearby_count"] / 8.0),
            "safety": self.needs.safety,
        }
        top_memories = self.memory.retrieve_similar(query_ctx, tick, top_k=8)
        by_action: dict[str, list[tuple[float, MemoryEntry]]] = {}
        for sim, mem in top_memories:
            by_action.setdefault(mem.event_type, []).append((sim, mem))
        return {"query_context": query_ctx, "top": top_memories, "by_action": by_action}

    def decide_action(
        self,
        observation: dict[str, Any],
        memory_context: dict[str, Any],
        learn_cfg: LearningConfig,
        rng: SeededRNG,
        tick: int,
    ) -> tuple[str, dict[str, Any]]:
        """Steps 4-7: evaluate actions, compute utility, select action with explainability."""
        action, explanation = select_action_with_explanation(
            agent=self,
            environment=observation,
            memory_context=memory_context,
            learn_cfg=learn_cfg,
            rng=rng,
            tick=tick,
        )
        self.last_action = action
        self.last_explanation = explanation
        self.decision_history.append(explanation)
        return action, explanation

    def apply_metabolic_decay(self, season_mult: float, hazard_level: float) -> None:
        """Advance age and natural need decay each tick."""
        self.age += 1
        self.needs.adjust("nutrition", -0.022 * season_mult)
        self.needs.adjust("energy", -0.018 * season_mult)
        self.needs.adjust("safety", -0.012 - 0.03 * hazard_level)
        self.needs.adjust("social_connection", -0.014)
        self.needs.adjust("belonging", -0.008)
        self.needs.adjust("achievement", -0.007)
        self.needs.adjust("knowledge_acquisition", -0.006)

        # Auto-consume carried food/water when nutrition drops
        if self.needs.nutrition < 0.62:
            if self.resources.get("food", 0.0) >= 0.35:
                self.resources["food"] -= 0.35
                self.needs.adjust("nutrition", 0.14)
            if self.resources.get("water", 0.0) >= 0.30:
                self.resources["water"] -= 0.30
                self.needs.adjust("nutrition", 0.08)

        # Update resource_security based on actual reserves
        total_res = sum(self.resources.values())
        sec_target = min(1.0, total_res / 18.0)
        self.needs.resource_security = 0.7 * self.needs.resource_security + 0.3 * sec_target
        self.needs.clamp_all()

    def update_goals_and_beliefs(self, tick: int, scarcity: float, outcome: float) -> None:
        self.beliefs["world.scarcity"].update(scarcity, tick, weight=0.2)
        if self.last_action == "cooperate":
            self.beliefs["world.cooperation_payoff"].update(max(0.0, min(1.0, 0.5 + outcome)), tick, weight=0.25)

        for g in self.goals:
            if g.goal_type == "survive":
                g.progress = min(1.0, 0.5 * self.needs.nutrition + 0.5 * self.needs.safety)
            elif g.goal_type == "prosper":
                g.progress = min(1.0, inventory_wealth(self.resources) / max(1.0, g.target_value))
            elif g.goal_type == "belong":
                g.progress = self.needs.belonging
            elif g.goal_type == "learn":
                g.progress = min(1.0, self.resources.get("knowledge", 0.0) / max(1.0, g.target_value))
            elif g.goal_type == "cooperate":
                g.progress = min(1.0, self.reputation)
            elif g.goal_type == "explore":
                g.progress = min(1.0, len(self.memory.semantic) / 10.0)

    def wealth(self, prices: dict[str, float] | None = None) -> float:
        return inventory_wealth(self.resources, prices)

    def to_summary_dict(self, prices: dict[str, float] | None = None) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "birth_tick": self.birth_tick,
            "age": self.age,
            "generation": self.generation,
            "occupation": self.occupation,
            "social_status": round(self.social_status, 4),
            "location_id": self.location_id,
            "community_id": self.community_id,
            "alive": self.alive,
            "reputation": round(self.reputation, 4),
            "last_action": self.last_action,
            "last_reward": round(self.last_reward, 4),
            "cumulative_reward": round(self.cumulative_reward, 4),
            "wealth": round(self.wealth(prices), 3),
            "mean_need_satisfaction": round(self.needs.mean_satisfaction(), 4),
            "traits": self.traits.to_dict(),
            "needs": self.needs.to_dict(),
            "cultural_traits": dict(self.cultural_traits),
        }

    def to_detail_dict(self, prices: dict[str, float] | None = None) -> dict[str, Any]:
        d = self.to_summary_dict(prices)
        d.update(
            {
                "home_location_id": self.home_location_id,
                "resources": {k: round(v, 4) for k, v in self.resources.items()},
                "goals": [g.to_dict() for g in self.goals],
                "beliefs": {k: v.to_dict() for k, v in self.beliefs.items()},
                "preferences": dict(self.preferences),
                "memory_summary": self.memory.summary(),
                "learning_summary": {
                    "total_updates": self.q_learner.total_updates,
                    "social_adoptions": self.q_learner.social_adoptions,
                    "mean_q_value": round(self.q_learner.mean_q_value(), 4),
                    "failure_counts": dict(self.q_learner.failure_counts),
                    "recent_records": [r.to_dict() for r in self.q_learner.recent_records[-12:]],
                },
                "last_explanation": self.last_explanation,
                "decision_history": list(self.decision_history),
            }
        )
        return d

    def to_snapshot_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "birth_tick": self.birth_tick,
            "age": self.age,
            "generation": self.generation,
            "occupation": self.occupation,
            "social_status": self.social_status,
            "location_id": self.location_id,
            "home_location_id": self.home_location_id,
            "community_id": self.community_id,
            "alive": self.alive,
            "traits": {
                "openness": self.traits.openness,
                "conscientiousness": self.traits.conscientiousness,
                "extraversion": self.traits.extraversion,
                "agreeableness": self.traits.agreeableness,
                "emotional_stability": self.traits.emotional_stability,
            },
            "needs": {n: float(getattr(self.needs, n)) for n in ("nutrition", "energy", "safety", "social_connection", "belonging", "achievement", "knowledge_acquisition", "resource_security")},
            "resources": dict(self.resources),
            "goals": [
                {
                    "goal_id": g.goal_id,
                    "goal_type": g.goal_type,
                    "target_value": g.target_value,
                    "priority": g.priority,
                    "progress": g.progress,
                    "active": g.active,
                }
                for g in self.goals
            ],
            "beliefs": {
                k: {
                    "belief_key": v.belief_key,
                    "value": v.value,
                    "confidence": v.confidence,
                    "updated_tick": v.updated_tick,
                }
                for k, v in self.beliefs.items()
            },
            "preferences": dict(self.preferences),
            "cultural_traits": dict(self.cultural_traits),
            "memory": self.memory.to_snapshot_dict(),
            "q_learner": self.q_learner.to_snapshot_dict(),
            "reputation": self.reputation,
            "last_action": self.last_action,
            "last_reward": self.last_reward,
            "cumulative_reward": self.cumulative_reward,
            "last_explanation": self.last_explanation,
            "decision_history": list(self.decision_history),
        }

    @classmethod
    def from_snapshot_dict(cls, d: dict[str, Any]) -> Agent:
        ag = cls(
            agent_id=d["agent_id"],
            name=d["name"],
            birth_tick=int(d["birth_tick"]),
            age=int(d["age"]),
            generation=int(d["generation"]),
            occupation=d["occupation"],
            social_status=float(d["social_status"]),
            location_id=d["location_id"],
            home_location_id=d["home_location_id"],
            community_id=d.get("community_id"),
            alive=bool(d.get("alive", True)),
            traits=BigFiveTraits.from_dict(d["traits"]),
            needs=AgentNeeds.from_dict(d["needs"]),
            resources={k: float(v) for k, v in d["resources"].items()},
            goals=[AgentGoal.from_dict(g) for g in d["goals"]],
            beliefs={k: AgentBelief.from_dict(v) for k, v in d["beliefs"].items()},
            preferences=dict(d.get("preferences", {})),
            cultural_traits=dict(d.get("cultural_traits", DEFAULT_CULTURAL_TRAITS)),
            memory=AgentMemory.from_dict(d["memory"]),
            q_learner=QLearningEngine.from_dict(d["q_learner"]),
            reputation=float(d.get("reputation", 0.5)),
            last_action=d.get("last_action", "rest"),
            last_reward=float(d.get("last_reward", 0.0)),
            cumulative_reward=float(d.get("cumulative_reward", 0.0)),
            last_explanation=dict(d.get("last_explanation", {})),
            decision_history=deque(d.get("decision_history", []), maxlen=40),
        )
        return ag

    @classmethod
    def spawn(
        cls,
        index: int,
        location_id: str,
        rng: SeededRNG,
        personality_means: dict[str, float] | None = None,
        personality_std: float = 0.16,
        initial_resource_mult: float = 1.0,
        memory_capacity: int = 80,
        birth_tick: int = 0,
        generation: int = 1,
    ) -> Agent:
        means = personality_means or {}
        traits = BigFiveTraits(
            openness=rng.normal_clipped(means.get("openness", 0.52), personality_std),
            conscientiousness=rng.normal_clipped(means.get("conscientiousness", 0.52), personality_std),
            extraversion=rng.normal_clipped(means.get("extraversion", 0.50), personality_std),
            agreeableness=rng.normal_clipped(means.get("agreeableness", 0.55), personality_std),
            emotional_stability=rng.normal_clipped(means.get("emotional_stability", 0.52), personality_std),
        )
        occupation = rng.choice(OCCUPATIONS)
        resources = {
            "food": round(rng.uniform(2.0, 4.5) * initial_resource_mult, 3),
            "water": round(rng.uniform(2.0, 4.5) * initial_resource_mult, 3),
            "raw_materials": round(rng.uniform(1.0, 3.0) * initial_resource_mult, 3),
            "tools": round((1.0 if occupation == "artisan" else rng.uniform(0.2, 1.0)) * initial_resource_mult, 3),
            "knowledge": round((1.5 if occupation == "scholar" else rng.uniform(0.2, 1.0)) * initial_resource_mult, 3),
            "energy": round(rng.uniform(1.5, 3.5) * initial_resource_mult, 3),
        }
        needs = AgentNeeds(
            nutrition=rng.uniform(0.65, 0.90),
            energy=rng.uniform(0.68, 0.92),
            safety=rng.uniform(0.65, 0.88),
            social_connection=rng.uniform(0.45, 0.78),
            belonging=rng.uniform(0.45, 0.75),
            achievement=rng.uniform(0.40, 0.70),
            knowledge_acquisition=rng.uniform(0.40, 0.72),
            resource_security=rng.uniform(0.45, 0.75),
        )
        goals = [
            AgentGoal(goal_id="g_survive", goal_type="survive", target_value=0.85, priority=0.90),
            AgentGoal(goal_id="g_prosper", goal_type="prosper", target_value=24.0, priority=0.65 + 0.2 * traits.conscientiousness),
            AgentGoal(goal_id="g_belong", goal_type="belong", target_value=0.80, priority=0.45 + 0.4 * traits.extraversion),
            AgentGoal(goal_id="g_learn", goal_type="learn", target_value=8.0, priority=0.40 + 0.45 * traits.openness),
        ]
        beliefs = {
            "world.scarcity": AgentBelief("world.scarcity", 0.35, 0.4, birth_tick),
            "world.cooperation_payoff": AgentBelief("world.cooperation_payoff", 0.50 + 0.2 * traits.agreeableness, 0.4, birth_tick),
            "norm.sharing_beneficial": AgentBelief("norm.sharing_beneficial", 0.45 + 0.25 * traits.agreeableness, 0.35, birth_tick),
        }
        cultural_traits = {
            "sharing_norm": "generous" if traits.agreeableness > 0.65 else ("hoarding" if traits.agreeableness < 0.35 else "balanced"),
            "work_ethic": "exploratory" if traits.openness > 0.68 else ("collaborative" if traits.extraversion > 0.62 else "industrious"),
            "conflict_style": "diplomatic" if traits.agreeableness > 0.55 else ("assertive" if traits.emotional_stability < 0.4 else "avoidant"),
            "governance_pref": "council" if traits.agreeableness > 0.52 else "market",
        }
        return cls(
            agent_id=f"ag_{index:04d}",
            name=generate_agent_name(index, rng),
            birth_tick=birth_tick,
            age=rng.randint(18, 38) if birth_tick == 0 else 0,
            generation=generation,
            occupation=occupation,
            social_status=round(rng.uniform(0.30, 0.65), 4),
            location_id=location_id,
            home_location_id=location_id,
            traits=traits,
            needs=needs,
            resources=resources,
            goals=goals,
            beliefs=beliefs,
            cultural_traits=cultural_traits,
            memory=AgentMemory(episodic_capacity=memory_capacity),
        )
