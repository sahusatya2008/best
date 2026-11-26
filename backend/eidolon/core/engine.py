"""Discrete-time simulation engine orchestrating the 12-stage EIDOLON tick pipeline."""

from __future__ import annotations

import hashlib
import json
import time
import zlib
from dataclasses import asdict, dataclass, field
from typing import Any

from eidolon.agent.cognition import Agent
from eidolon.agent.learning import LearningConfig
from eidolon.agent.memory import MemoryEntry
from eidolon.core.clock import SimulationClock
from eidolon.core.events import EventBus, SimulationEvent
from eidolon.core.rng import SeededRNG
from eidolon.social.communication import exchange_information
from eidolon.social.culture import attempt_cultural_transmission, measure_cultural_metrics
from eidolon.social.institutions import InstitutionRegistry
from eidolon.social.relationships import SocialNetwork
from eidolon.world.economy import EconomicLedger
from eidolon.world.environment import SEASON_METABOLIC_MULTIPLIER, EnvironmentState
from eidolon.world.grid import WorldGrid
from eidolon.world.resources import transfer_resource


@dataclass
class ExperimentConfig:
    """Complete scientific configuration governing an EIDOLON simulation."""

    scenario_id: str = "cooperation_experiment"
    name: str = "Cooperation Experiment"
    description: str = ""
    seed: int = 42
    population_size: int = 100
    num_locations: int = 16
    duration_ticks: int = 300

    # Environment & Economy
    initial_resource_richness: float = 1.0
    scarcity: float = 0.15
    climate_severity: float = 0.10
    regeneration_scale: float = 1.0
    env_event_probability: float = 0.04

    # Learning & Memory
    learning_rate: float = 0.15
    discount_factor: float = 0.90
    exploration_rate: float = 0.12
    social_learning_prob: float = 0.25
    adaptation_speed: float = 1.0
    memory_capacity: int = 80

    # Social, Culture & Institutions
    cooperation_reward: float = 0.28
    social_interaction_prob: float = 0.85
    cultural_transmission_rate: float = 0.28
    institutions_enabled: bool = True
    institution_formation_threshold: float = 0.58

    # Population Personality Priors
    personality_means: dict[str, float] = field(
        default_factory=lambda: {
            "openness": 0.52,
            "conscientiousness": 0.54,
            "extraversion": 0.52,
            "agreeableness": 0.56,
            "emotional_stability": 0.54,
        }
    )
    personality_std: float = 0.16

    def to_learning_config(self) -> LearningConfig:
        return LearningConfig(
            learning_rate=self.learning_rate,
            discount_factor=self.discount_factor,
            exploration_rate=self.exploration_rate,
            social_learning_prob=self.social_learning_prob,
            adaptation_speed=self.adaptation_speed,
            memory_capacity=self.memory_capacity,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> ExperimentConfig:
        valid = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in d.items() if k in valid}
        return cls(**filtered)


class SimulationEngine:
    """Authoritative, deterministic, local-first artificial society engine."""

    def __init__(
        self,
        experiment_id: str,
        config: ExperimentConfig,
        clock: SimulationClock | None = None,
        rng: SeededRNG | None = None,
        world: WorldGrid | None = None,
        environment: EnvironmentState | None = None,
        economy: EconomicLedger | None = None,
        agents: dict[str, Agent] | None = None,
        network: SocialNetwork | None = None,
        institutions: InstitutionRegistry | None = None,
    ) -> None:
        self.experiment_id = experiment_id
        self.config = config
        self.clock = clock or SimulationClock()
        self.rng = rng or SeededRNG(config.seed)
        self.world = world or WorldGrid.generate(
            rng=self.rng,
            num_locations=config.num_locations,
            resource_richness=config.initial_resource_richness,
            scarcity=config.scarcity,
        )
        self.environment = environment or EnvironmentState(
            climate_severity=config.climate_severity,
            regeneration_scale=config.regeneration_scale,
            event_probability=config.env_event_probability,
        )
        self.economy = economy or EconomicLedger()
        self.network = network or SocialNetwork()
        self.institutions = institutions or InstitutionRegistry()
        self.events = EventBus(max_recent=2500)

        self.agents: dict[str, Agent] = agents or {}
        if not self.agents:
            self._spawn_initial_population()

        # Metrics history & diagnostics
        self.metrics_history: list[dict[str, Any]] = []
        self.total_interactions: int = 0
        self.total_cooperations: int = 0
        self.total_competitions: int = 0
        self.collective_attempts: int = 0
        self.collective_successes: int = 0
        self.last_tick_ms: float = 0.0
        self.avg_tick_ms: float = 0.0
        self.detected_patterns: list[dict[str, Any]] = []
        self._last_cultural_metrics: dict[str, Any] = measure_cultural_metrics(
            list(self.agents.values()), self.network.communities
        )

    def _spawn_initial_population(self) -> None:
        loc_ids = sorted(self.world.locations.keys())
        init_res_mult = max(0.3, self.config.initial_resource_richness * (1.0 - 0.5 * self.config.scarcity))
        for i in range(self.config.population_size):
            loc_id = loc_ids[i % len(loc_ids)]
            ag = Agent.spawn(
                index=i + 1,
                location_id=loc_id,
                rng=self.rng,
                personality_means=self.config.personality_means,
                personality_std=self.config.personality_std,
                initial_resource_mult=init_res_mult,
                memory_capacity=self.config.memory_capacity,
                birth_tick=0,
                generation=1,
            )
            self.agents[ag.agent_id] = ag

    def _group_by_location(self) -> dict[str, list[Agent]]:
        by_loc: dict[str, list[Agent]] = {lid: [] for lid in self.world.locations}
        for ag in self.agents.values():
            if ag.alive:
                by_loc.setdefault(ag.location_id, []).append(ag)
        return by_loc

    def step(self) -> dict[str, Any]:
        """Execute one complete deterministic discrete-time simulation tick."""
        t0 = time.perf_counter()
        tick = self.clock.advance()
        learn_cfg = self.config.to_learning_config()
        self.economy.reset_tick_counters()

        # 1. ENVIRONMENT UPDATE
        env_events = self.environment.step(self.world, self.clock, self.rng)
        for ev in env_events:
            self.events.emit(
                SimulationEvent(
                    tick=tick,
                    event_type=ev["event_type"],
                    location_id=ev["location_id"],
                    payload=ev,
                )
            )

        # Build spatial index
        agents_by_loc = self._group_by_location()
        season_mult = SEASON_METABOLIC_MULTIPLIER[self.clock.season]
        ordered_ids = sorted(aid for aid, ag in self.agents.items() if ag.alive)

        # 2-5. PERCEPTION, NEED EVALUATION, MEMORY RETRIEVAL, DECISION MAKING
        observations: dict[str, dict[str, Any]] = {}
        chosen_actions: dict[str, str] = {}
        explanations: dict[str, dict[str, Any]] = {}

        for aid in ordered_ids:
            ag = self.agents[aid]
            loc = self.world.locations[ag.location_id]
            ag.apply_metabolic_decay(season_mult, loc.hazard_level)
            local_stocks = {r: s.quantity for r, s in loc.resources.items()}
            local_max = {r: s.max_capacity for r, s in loc.resources.items()}
            nearby = [other for other in agents_by_loc.get(ag.location_id, []) if other.agent_id != aid]
            best_trust = self.network.best_local_trust(aid, [o.agent_id for o in nearby])
            in_inst = self.institutions.get_for_agent(aid) is not None

            obs = ag.perceive(
                local_stocks=local_stocks,
                local_max=local_max,
                hazard_level=loc.hazard_level,
                location_kind=loc.kind,
                neighbors=loc.neighbors,
                nearby_agents=nearby,
                best_partner_trust=best_trust,
                cooperation_reward=self.config.cooperation_reward,
                in_institution=in_inst,
            )
            mem_ctx = ag.retrieve_memory_context(obs, tick)
            action, expl = ag.decide_action(obs, mem_ctx, learn_cfg, self.rng, tick)
            observations[aid] = obs
            chosen_actions[aid] = action
            explanations[aid] = expl

        # 6-8. ACTION EXECUTION, TRANSACTIONAL RESOURCE SETTLEMENT & SOCIAL INTERACTIONS
        tick_coops = 0
        tick_social_acts = 0
        tick_utilities: list[float] = []
        tick_rewards: dict[str, float] = {aid: 0.0 for aid in ordered_ids}

        for aid in ordered_ids:
            ag = self.agents[aid]
            loc = self.world.locations[ag.location_id]
            action = chosen_actions[aid]
            expl = explanations[aid]
            tick_utilities.append(float(expl["selected_utility"]))
            nearby = [o for o in agents_by_loc.get(ag.location_id, []) if o.agent_id != aid]
            inst = self.institutions.get_for_agent(aid)

            outcome = 0.0
            target_id: str | None = None
            tool_bonus = 1.0 + min(0.6, ag.resources.get("tools", 0.0) * 0.25)

            if action == "harvest_food":
                taken = loc.resources["food"].withdraw(1.25 * tool_bonus)
                ag.resources["food"] += taken
                self.economy.total_produced += taken
                if taken >= 0.4:
                    consumed = min(taken, 0.7)
                    ag.resources["food"] -= consumed
                    self.economy.total_consumed += consumed
                    ag.needs.adjust("nutrition", 0.16 * (consumed / 0.7))
                    ag.needs.adjust("energy", -0.04)
                    outcome = 0.28 + 0.12 * (taken / 1.5)
                else:
                    outcome = -0.18

            elif action == "gather_water":
                taken = loc.resources["water"].withdraw(1.30 * tool_bonus)
                ag.resources["water"] += taken
                self.economy.total_produced += taken
                if taken >= 0.4:
                    consumed = min(taken, 0.65)
                    ag.resources["water"] -= consumed
                    self.economy.total_consumed += consumed
                    ag.needs.adjust("nutrition", 0.11 * (consumed / 0.65))
                    ag.needs.adjust("safety", 0.04)
                    ag.needs.adjust("energy", -0.03)
                    outcome = 0.25
                else:
                    outcome = -0.15

            elif action == "extract_materials":
                m_taken = loc.resources["raw_materials"].withdraw(1.0 * tool_bonus)
                e_taken = loc.resources["energy"].withdraw(0.8 * tool_bonus)
                ag.resources["raw_materials"] += m_taken
                ag.resources["energy"] += e_taken
                self.economy.total_produced += (m_taken + e_taken)
                ag.needs.adjust("energy", -0.06)
                ag.needs.adjust("achievement", 0.06)
                outcome = 0.22 if (m_taken + e_taken) > 0.6 else -0.14

            elif action == "craft_tools":
                if ag.resources.get("raw_materials", 0.0) >= 1.0 and ag.resources.get("energy", 0.0) >= 0.5:
                    ag.resources["raw_materials"] -= 1.0
                    ag.resources["energy"] -= 0.5
                    crafted = 0.8 + 0.3 * ag.traits.conscientiousness
                    ag.resources["tools"] += crafted
                    self.economy.total_produced += crafted
                    ag.needs.adjust("achievement", 0.14)
                    ag.needs.adjust("energy", -0.05)
                    outcome = 0.36
                else:
                    outcome = -0.20

            elif action == "research_knowledge":
                bonus = 1.35 if loc.kind == "sanctuary" else 1.0
                if inst and inst.inst_type == "academy":
                    bonus += inst.rules.get("knowledge_bonus", 0.25)
                k_avail = loc.resources["knowledge"].withdraw(0.85 * bonus)
                gained = 0.45 * bonus + 0.5 * k_avail
                ag.resources["knowledge"] += gained
                self.economy.total_produced += gained
                ag.needs.adjust("knowledge_acquisition", 0.18)
                ag.needs.adjust("achievement", 0.06)
                ag.needs.adjust("energy", -0.03)
                outcome = 0.30

            elif action == "cooperate":
                if nearby and self.rng.random() <= self.config.social_interaction_prob:
                    # Prefer higher-trust or same-institution partner
                    partner = max(
                        nearby,
                        key=lambda p: self.network.get_trust(aid, p.agent_id, 0.5)
                        + (0.15 if inst and p.agent_id in inst.members else 0.0),
                    )
                    target_id = partner.agent_id
                    self.total_interactions += 1
                    tick_social_acts += 1
                    self.collective_attempts += 1

                    # Cooperative mutual surplus or joint harvest
                    shared = 0.0
                    for r in ("food", "water", "raw_materials", "knowledge"):
                        if ag.resources.get(r, 0.0) > 2.2:
                            shared += transfer_resource(ag.resources, partner.resources, r, 0.45)

                    # Joint production synergy when cooperating
                    synergy = self.config.cooperation_reward * (0.6 + 0.4 * partner.traits.agreeableness)
                    if inst and inst.inst_type == "resource_pool":
                        synergy += 0.12
                    joint_food = loc.resources["food"].withdraw(0.65)
                    ag.resources["food"] += joint_food * 0.5 + synergy * 0.6
                    partner.resources["food"] += joint_food * 0.5 + synergy * 0.6
                    self.economy.total_produced += joint_food + synergy * 1.2

                    ag.needs.adjust("social_connection", 0.14)
                    ag.needs.adjust("belonging", 0.14)
                    partner.needs.adjust("social_connection", 0.12)
                    partner.needs.adjust("belonging", 0.12)
                    ag.reputation = min(1.0, ag.reputation + 0.025)
                    partner.reputation = min(1.0, partner.reputation + 0.015)

                    self.network.record_interaction(aid, partner.agent_id, "cooperate", tick)
                    attempt_cultural_transmission(
                        ag, partner, self.network.get_trust(aid, partner.agent_id), self.config.cultural_transmission_rate, self.rng
                    )

                    tick_coops += 1
                    self.total_cooperations += 1
                    self.collective_successes += 1
                    outcome = 0.25 + synergy + 0.12 * (1.0 if shared > 0 else 0.0)
                    tick_rewards[partner.agent_id] += 0.15 * synergy
                else:
                    outcome = -0.10

            elif action == "trade":
                if nearby and self.rng.random() <= self.config.social_interaction_prob:
                    surplus_res = max(ag.resources.items(), key=lambda kv: kv[1])[0]
                    need_res = "food" if ag.needs.nutrition < 0.6 else min(ag.resources.items(), key=lambda kv: kv[1])[0]
                    partner = max(nearby, key=lambda p: p.resources.get(need_res, 0.0))
                    target_id = partner.agent_id
                    trade_res = self.economy.execute_bilateral_trade(
                        buyer_inv=ag.resources,
                        seller_inv=partner.resources,
                        wanted_resource=need_res,
                        offered_resource=surplus_res,
                        desired_amount=1.4,
                    )
                    self.total_interactions += 1
                    tick_social_acts += 1
                    if trade_res:
                        self.network.record_interaction(aid, partner.agent_id, "trade", tick)
                        ag.needs.adjust("resource_security", 0.12)
                        ag.needs.adjust("social_connection", 0.06)
                        partner.needs.adjust("resource_security", 0.10)
                        ag.reputation = min(1.0, ag.reputation + 0.012)
                        outcome = 0.30
                    else:
                        outcome = -0.08
                else:
                    outcome = -0.08

            elif action == "compete":
                if nearby:
                    # Target weakest or rival agent
                    target = min(nearby, key=lambda p: self.network.get_trust(aid, p.agent_id, 0.5))
                    target_id = target.agent_id
                    self.total_interactions += 1
                    tick_social_acts += 1
                    self.total_competitions += 1

                    # Contested resource transfer (bounded & zero-sum + friction cost)
                    contested_res = max(target.resources.items(), key=lambda kv: kv[1])[0]
                    strength_a = 0.5 + 0.3 * ag.resources.get("tools", 0.0) + 0.2 * (1.0 - ag.traits.agreeableness)
                    strength_b = 0.5 + 0.3 * target.resources.get("tools", 0.0) + 0.2 * target.traits.emotional_stability
                    if strength_a >= strength_b:
                        seized = transfer_resource(target.resources, ag.resources, contested_res, 0.75)
                        ag.needs.adjust("achievement", 0.08)
                        target.needs.adjust("safety", -0.14)
                        outcome = 0.18 if seized > 0.2 else -0.12
                    else:
                        ag.needs.adjust("safety", -0.10)
                        outcome = -0.26

                    ag.reputation = max(0.0, ag.reputation - 0.04)
                    self.network.record_interaction(aid, target.agent_id, "compete", tick)
                    if inst and target.agent_id in inst.members:
                        self.institutions.record_violation(aid)
                else:
                    outcome = -0.14

            elif action == "communicate":
                if nearby:
                    partner = self.rng.choice(nearby)
                    target_id = partner.agent_id
                    self.total_interactions += 1
                    tick_social_acts += 1
                    msg = exchange_information(ag, partner, self.network, tick, observations[aid]["local_stocks"])
                    attempt_cultural_transmission(
                        ag,
                        partner,
                        self.network.get_trust(aid, partner.agent_id),
                        self.config.cultural_transmission_rate,
                        self.rng,
                    )
                    if ag.resources.get("knowledge", 0.0) > partner.resources.get("knowledge", 0.0) + 1.0:
                        self.network.record_interaction(aid, partner.agent_id, "mentor", tick)
                    self.events.emit(
                        SimulationEvent(
                            tick=tick,
                            event_type="communication",
                            actor_id=aid,
                            target_id=target_id,
                            location_id=ag.location_id,
                            payload=msg.to_dict(),
                        )
                    )
                    outcome = 0.16 if msg.msg_type != "disagreement" else -0.04
                else:
                    outcome = -0.06

            elif action == "migrate":
                if loc.neighbors:
                    # Prefer neighbor with known higher stock or lower hazard
                    best_nbr = max(
                        loc.neighbors,
                        key=lambda nid: (
                            sum(s.quantity for s in self.world.locations[nid].resources.values())
                            * (1.0 - self.world.locations[nid].hazard_level)
                            + self.rng.uniform(0.0, 25.0)
                        ),
                    )
                    old_loc = ag.location_id
                    ag.location_id = best_nbr
                    ag.needs.adjust("energy", -0.08)
                    ag.needs.adjust("safety", 0.07)
                    self.events.emit(
                        SimulationEvent(
                            tick=tick,
                            event_type="migration",
                            actor_id=aid,
                            location_id=best_nbr,
                            payload={"from_location": old_loc, "to_location": best_nbr},
                        )
                    )
                    outcome = 0.14
                else:
                    outcome = -0.10

            elif action == "rest":
                recovery = 0.24 if loc.kind in ("settlement", "sanctuary") else 0.17
                ag.needs.adjust("energy", recovery)
                ag.needs.adjust("safety", 0.08)
                outcome = 0.14

            tick_rewards[aid] += outcome

            # Emit primary agent decision event with full explanation payload
            if tick <= 50 or tick % 2 == 0 or action in ("cooperate", "trade", "compete", "migrate"):
                self.events.emit(
                    SimulationEvent(
                        tick=tick,
                        event_type=f"action_{action}",
                        actor_id=aid,
                        target_id=target_id,
                        location_id=ag.location_id,
                        payload={"outcome": round(outcome, 4), "location_id": ag.location_id},
                        explanation=expl,
                    )
                )

        # Refresh spatial index after potential migrations
        agents_by_loc = self._group_by_location()

        # Institutional formation & operational step
        new_insts = self.institutions.try_form_institutions(
            agents_by_location=agents_by_loc,
            network=self.network,
            tick=tick,
            enabled=self.config.institutions_enabled,
            min_trust_threshold=self.config.institution_formation_threshold,
        )
        for ni in new_insts:
            self.events.emit(
                SimulationEvent(
                    tick=tick,
                    event_type="institution_formed",
                    actor_id=ni.founder_id,
                    location_id=ni.location_id,
                    payload=ni.to_dict(),
                )
            )
        inst_events = self.institutions.step_institutions(self.agents, tick)
        for ie in inst_events:
            self.events.emit(
                SimulationEvent(
                    tick=tick,
                    event_type=ie["event_type"],
                    payload=ie,
                )
            )

        # 9. LEARNING UPDATE & MEMORY RECORDING / CONSOLIDATION
        q_vals_sample: list[float] = []
        for aid in ordered_ids:
            ag = self.agents[aid]
            action = chosen_actions[aid]
            obs = observations[aid]
            post_sat = ag.needs.mean_satisfaction()
            delta_sat = post_sat - ag.pending_pre_satisfaction
            reward = round(tick_rewards[aid] + 1.2 * delta_sat, 4)

            ag.last_reward = reward
            ag.cumulative_reward += reward
            ag.needs.clamp_all()
            ag.update_goals_and_beliefs(tick, obs["scarcity"], reward)

            next_state_key = ag.compute_state_key(obs["scarcity"], obs["nearby_count"])
            ag.q_learner.update(
                tick=tick,
                state_key=ag.pending_state_key,
                action=action,
                reward=reward,
                next_state_key=next_state_key,
                cfg=learn_cfg,
            )

            # Social learning from successful nearby agents
            nearby = agents_by_loc.get(ag.location_id, [])
            if nearby and self.rng.random() < learn_cfg.social_learning_prob:
                role_model = max(nearby, key=lambda o: o.last_reward)
                if role_model.agent_id != aid and role_model.last_reward > ag.last_reward + 0.05:
                    trust = self.network.get_trust(aid, role_model.agent_id, 0.5)
                    ag.q_learner.social_learn(
                        tick=tick,
                        state_key=next_state_key,
                        observed_action=role_model.last_action,
                        observed_reward=role_model.last_reward,
                        trust_in_model=trust,
                        cfg=learn_cfg,
                    )

            # Store episodic memory
            _, urg = ag.needs.most_urgent()
            ag.memory.record_experience(
                MemoryEntry(
                    tick=tick,
                    layer="episodic",
                    event_type=action,
                    participants=[explanations[aid].get("target_id")] if explanations[aid].get("target_id") else [],
                    context={
                        "location_id": ag.location_id,
                        "need_urgency": round(urg, 3),
                        "scarcity": round(obs["scarcity"], 3),
                        "social_density": round(min(1.0, obs["nearby_count"] / 8.0), 3),
                        "safety": round(ag.needs.safety, 3),
                    },
                    outcome=reward,
                    emotional_significance=min(1.0, abs(reward) + 0.25),
                    relevance_weight=1.0,
                )
            )
            if tick % 10 == 0:
                ag.memory.consolidate(tick)
            q_vals_sample.append(ag.q_learner.mean_q_value())

        # 10. ECONOMY & SOCIAL NETWORK MAINTENANCE & METRICS UPDATE
        alive_agents = [self.agents[aid] for aid in ordered_ids]
        inventories = [ag.resources for ag in alive_agents]
        self.economy.update_market_prices(inventories, len(alive_agents))

        if tick % 10 == 0 or tick == 1:
            self.network.decay_stale_edges(tick)
            self.network.detect_communities(self.agents, self.world.locations, tick)
            self._last_cultural_metrics = measure_cultural_metrics(alive_agents, self.network.communities)

        coop_index = (tick_coops / tick_social_acts) if tick_social_acts > 0 else (
            self.total_cooperations / max(1, self.total_interactions)
        )
        gini = self.economy.compute_gini(inventories)
        world_res = sum(self.world.total_resources().values())
        agent_res = sum(sum(inv.values()) for inv in inventories)
        mean_trust = self.network.mean_trust()
        net_density = self.network.network_density(len(alive_agents))
        mean_q = sum(q_vals_sample) / len(q_vals_sample) if q_vals_sample else 0.0
        mean_u = sum(tick_utilities) / len(tick_utilities) if tick_utilities else 0.0
        coll_rate = self.collective_successes / max(1, self.collective_attempts)
        avg_need = sum(ag.needs.mean_satisfaction() for ag in alive_agents) / max(1, len(alive_agents))

        metric_row = {
            "tick": tick,
            "population": len(alive_agents),
            "total_resources": round(world_res + agent_res, 3),
            "cooperation_index": round(coop_index, 4),
            "gini_coefficient": round(gini, 4),
            "mean_trust": round(mean_trust, 4),
            "network_density": round(net_density, 4),
            "community_count": len(self.network.communities),
            "institution_count": len(self.institutions.active_list()),
            "cultural_diversity": round(self._last_cultural_metrics["cultural_diversity"], 4),
            "mean_q_value": round(mean_q, 4),
            "mean_utility": round(mean_u, 4),
            "trade_volume": round(self.economy.tick_trade_volume, 4),
            "collective_success_rate": round(coll_rate, 4),
            "avg_need_satisfaction": round(avg_need, 4),
        }
        self.metrics_history.append(metric_row)

        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        self.last_tick_ms = elapsed_ms
        self.avg_tick_ms = elapsed_ms if self.avg_tick_ms == 0.0 else (0.85 * self.avg_tick_ms + 0.15 * elapsed_ms)
        return metric_row

    def state_summary(self) -> dict[str, Any]:
        latest = self.metrics_history[-1] if self.metrics_history else {
            "tick": self.clock.tick,
            "population": len(self.agents),
            "total_resources": round(sum(self.world.total_resources().values()), 3),
            "cooperation_index": 0.0,
            "gini_coefficient": 0.0,
            "mean_trust": 0.5,
            "network_density": 0.0,
            "community_count": 0,
            "institution_count": 0,
            "cultural_diversity": self._last_cultural_metrics.get("cultural_diversity", 0.0),
            "mean_q_value": 0.0,
            "mean_utility": 0.0,
            "trade_volume": 0.0,
            "collective_success_rate": 0.0,
            "avg_need_satisfaction": 0.65,
        }
        return {
            "experiment_id": self.experiment_id,
            "config": self.config.to_dict(),
            "clock": self.clock.to_dict(),
            "environment": self.environment.to_dict(),
            "economy": self.economy.to_dict(),
            "metrics": latest,
            "cultural_metrics": self._last_cultural_metrics,
            "total_interactions": self.total_interactions,
            "total_cooperations": self.total_cooperations,
            "total_competitions": self.total_competitions,
            "performance": {
                "last_tick_ms": round(self.last_tick_ms, 3),
                "avg_tick_ms": round(self.avg_tick_ms, 3),
            },
        }

    def to_snapshot_bytes(self) -> tuple[bytes, str]:
        """Serialize complete deterministic state to compressed JSON + SHA-256 checksum."""
        payload = {
            "experiment_id": self.experiment_id,
            "config": self.config.to_dict(),
            "clock": self.clock.to_dict(),
            "rng": self.rng.get_state(),
            "world": self.world.to_snapshot_dict(),
            "environment": self.environment.to_dict(),
            "economy": self.economy.to_snapshot_dict(),
            "network": self.network.to_snapshot_dict(),
            "institutions": self.institutions.to_snapshot_dict(),
            "agents": [self.agents[aid].to_snapshot_dict() for aid in sorted(self.agents.keys())],
            "metrics_history": self.metrics_history,
            "cultural_metrics": self._last_cultural_metrics,
            "total_interactions": self.total_interactions,
            "total_cooperations": self.total_cooperations,
            "total_competitions": self.total_competitions,
            "collective_attempts": self.collective_attempts,
            "collective_successes": self.collective_successes,
        }
        raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        compressed = zlib.compress(raw, level=6)
        checksum = hashlib.sha256(compressed).hexdigest()
        return compressed, checksum

    @classmethod
    def from_snapshot_bytes(cls, blob: bytes, checksum: str | None = None) -> SimulationEngine:
        if checksum:
            actual = hashlib.sha256(blob).hexdigest()
            if actual != checksum:
                raise ValueError("Snapshot checksum mismatch — corrupted snapshot data.")
        raw = zlib.decompress(blob)
        data = json.loads(raw.decode("utf-8"))
        config = ExperimentConfig.from_dict(data["config"])
        clock = SimulationClock.from_dict(data["clock"])
        rng = SeededRNG.from_state(data["rng"])
        world = WorldGrid.from_dict(data["world"])
        environment = EnvironmentState.from_dict(data["environment"])
        economy = EconomicLedger.from_snapshot_dict(data["economy"])
        network = SocialNetwork.from_dict(data["network"])
        institutions = InstitutionRegistry.from_dict(data["institutions"])
        agents = {ad["agent_id"]: Agent.from_snapshot_dict(ad) for ad in data["agents"]}

        eng = cls(
            experiment_id=data["experiment_id"],
            config=config,
            clock=clock,
            rng=rng,
            world=world,
            environment=environment,
            economy=economy,
            agents=agents,
            network=network,
            institutions=institutions,
        )
        eng.metrics_history = list(data.get("metrics_history", []))
        if "cultural_metrics" in data:
            eng._last_cultural_metrics = data["cultural_metrics"]
        eng.total_interactions = int(data.get("total_interactions", 0))
        eng.total_cooperations = int(data.get("total_cooperations", 0))
        eng.total_competitions = int(data.get("total_competitions", 0))
        eng.collective_attempts = int(data.get("collective_attempts", 0))
        eng.collective_successes = int(data.get("collective_successes", 0))
        return eng
