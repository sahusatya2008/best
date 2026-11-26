"""Tests for Q-learning convergence, social learning, failure adaptation, and fixed-seed reproducibility."""

from eidolon.agent.cognition import Agent
from eidolon.agent.learning import LearningConfig, QLearningEngine
from eidolon.agent.reasoning import calculate_action_utility
from eidolon.core.engine import ExperimentConfig, SimulationEngine
from eidolon.core.rng import SeededRNG


def test_q_learning_and_failure_adaptation_change_utility():
    rng = SeededRNG(5)
    ag = Agent.spawn(1, "loc_00", rng)
    cfg = LearningConfig(learning_rate=0.35, discount_factor=0.9)
    state_key = "nutrition|low|social|rested"

    env = {
        "local_stocks": {"food": 30.0, "water": 30.0, "raw_materials": 20.0, "tools": 5.0, "knowledge": 10.0, "energy": 20.0},
        "nearby_count": 3,
        "best_partner_trust": 0.6,
        "hazard_level": 0.05,
        "cooperation_reward": 0.3,
        "scarcity": 0.2,
        "in_institution": False,
        "state_key": state_key,
        "location_kind": "settlement",
        "neighbors": ["loc_01"],
    }
    before_coop = calculate_action_utility("cooperate", ag, env, {}).total_utility
    for tick in range(1, 10):
        ag.q_learner.update(tick, state_key, "cooperate", 0.8, state_key, cfg)
    after_coop = calculate_action_utility("cooperate", ag, env, {}).total_utility
    assert after_coop > before_coop

    # Failure adaptation reduces utility of penalized action
    before_comp = calculate_action_utility("compete", ag, env, {}).total_utility
    for tick in range(10, 15):
        ag.q_learner.update(tick, state_key, "compete", -0.5, state_key, cfg)
    after_comp = calculate_action_utility("compete", ag, env, {}).total_utility
    assert ag.q_learner.failure_counts["compete"] == 5
    assert after_comp < before_comp


def test_social_learning_adoption():
    q = QLearningEngine()
    cfg = LearningConfig(learning_rate=0.3)
    rec = q.social_learn(tick=5, state_key="s1", observed_action="trade", observed_reward=0.6, trust_in_model=0.9, cfg=cfg)
    assert rec is not None
    assert q.get_q("s1", "trade") > 0.0
    assert q.social_adoptions == 1


def test_fixed_seed_reproducibility():
    cfg1 = ExperimentConfig(population_size=35, seed=1234, duration_ticks=30)
    cfg2 = ExperimentConfig(population_size=35, seed=1234, duration_ticks=30)

    e1 = SimulationEngine("repro_1", cfg1)
    e2 = SimulationEngine("repro_2", cfg2)

    for _ in range(30):
        e1.step()
        e2.step()

    assert e1.metrics_history == e2.metrics_history
    assert e1.total_interactions == e2.total_interactions
    assert e1.total_cooperations == e2.total_cooperations
    for aid in e1.agents:
        assert e1.agents[aid].location_id == e2.agents[aid].location_id
        assert e1.agents[aid].last_action == e2.agents[aid].last_action
        assert abs(e1.agents[aid].cumulative_reward - e2.agents[aid].cumulative_reward) < 1e-9
