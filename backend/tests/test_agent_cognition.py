"""Tests for Agent Cognitive Architecture: personality weights, memory layers, and explainability."""

from eidolon.agent.cognition import Agent
from eidolon.agent.memory import AgentMemory, MemoryEntry
from eidolon.agent.reasoning import calculate_action_utility
from eidolon.core.rng import SeededRNG


def test_personality_influences_utility_mathematically():
    rng = SeededRNG(12)
    coop_agent = Agent.spawn(1, "loc_00", rng, personality_means={"agreeableness": 0.95, "extraversion": 0.85}, personality_std=0.01)
    comp_agent = Agent.spawn(2, "loc_00", rng, personality_means={"agreeableness": 0.08, "emotional_stability": 0.10}, personality_std=0.01)

    env = {
        "local_stocks": {"food": 20.0, "water": 20.0, "raw_materials": 15.0, "tools": 5.0, "knowledge": 10.0, "energy": 15.0},
        "nearby_count": 3,
        "best_partner_trust": 0.75,
        "hazard_level": 0.05,
        "cooperation_reward": 0.3,
        "scarcity": 0.2,
        "in_institution": False,
        "state_key": "test",
        "location_kind": "settlement",
        "neighbors": ["loc_01"],
    }
    u_coop_high = calculate_action_utility("cooperate", coop_agent, env, {})
    u_coop_low = calculate_action_utility("cooperate", comp_agent, env, {})
    assert u_coop_high.personality_bias > u_coop_low.personality_bias
    assert u_coop_high.total_utility > u_coop_low.total_utility


def test_four_layer_memory_retrieval_and_consolidation():
    mem = AgentMemory(episodic_capacity=20)
    for t in range(1, 6):
        mem.record_experience(
            MemoryEntry(
                tick=t,
                layer="episodic",
                event_type="cooperate",
                participants=["ag_0002"],
                context={"location_id": "loc_00", "need_urgency": 0.6, "scarcity": 0.3, "social_density": 0.5, "safety": 0.8},
                outcome=0.45,
                emotional_significance=0.75,
            )
        )
    assert len(mem.working) == 5
    assert len(mem.episodic) == 5
    assert "cooperate" in mem.procedural

    hits = mem.retrieve_similar(
        {"location_id": "loc_00", "need_urgency": 0.62, "scarcity": 0.32, "social_density": 0.5, "safety": 0.8},
        current_tick=6,
        top_k=3,
    )
    assert len(hits) == 3
    assert hits[0][0] > 0.5

    extracted = mem.consolidate(current_tick=6)
    assert extracted >= 1
    assert "pattern.cooperate.expected_outcome" in mem.semantic
    assert abs(mem.semantic["pattern.cooperate.expected_outcome"]["value"] - 0.45) < 1e-3
