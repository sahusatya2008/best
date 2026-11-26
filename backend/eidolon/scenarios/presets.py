"""Eight prebuilt scientific scenarios with distinct parameterized hypotheses."""

from __future__ import annotations

from typing import Any

from eidolon.core.engine import ExperimentConfig

SCENARIO_DEFINITIONS: dict[str, dict[str, Any]] = {
    "cooperation_experiment": {
        "scenario_id": "cooperation_experiment",
        "title": "1. The Cooperation Experiment",
        "research_question": "Under what payoff synergies and interaction rates do cooperative clusters and mutual aid norms stabilize?",
        "config": ExperimentConfig(
            scenario_id="cooperation_experiment",
            name="The Cooperation Experiment",
            description="Investigates emergence and persistence of cooperative clusters under positive synergy rewards.",
            seed=42,
            population_size=100,
            duration_ticks=300,
            initial_resource_richness=1.0,
            scarcity=0.18,
            cooperation_reward=0.40,
            social_interaction_prob=0.90,
            institutions_enabled=True,
            personality_means={"openness": 0.52, "conscientiousness": 0.55, "extraversion": 0.58, "agreeableness": 0.62, "emotional_stability": 0.56},
        ),
    },
    "scarcity_experiment": {
        "scenario_id": "scarcity_experiment",
        "title": "2. The Scarcity Experiment",
        "research_question": "How does acute resource scarcity shift the balance between competition, hoarding, inequality, and mutual aid?",
        "config": ExperimentConfig(
            scenario_id="scarcity_experiment",
            name="The Scarcity Experiment",
            description="Studies agent competition, Gini inequality, and resource security under constrained supply.",
            seed=108,
            population_size=100,
            duration_ticks=300,
            initial_resource_richness=0.58,
            scarcity=0.68,
            climate_severity=0.35,
            regeneration_scale=0.65,
            cooperation_reward=0.14,
            social_interaction_prob=0.80,
            institutions_enabled=True,
            personality_means={"openness": 0.50, "conscientiousness": 0.55, "extraversion": 0.48, "agreeableness": 0.44, "emotional_stability": 0.46},
        ),
    },
    "cultural_transmission": {
        "scenario_id": "cultural_transmission",
        "title": "3. The Cultural Transmission Experiment",
        "research_question": "How do behavioural norms diffuse across spatial clusters and diverge between isolated communities?",
        "config": ExperimentConfig(
            scenario_id="cultural_transmission",
            name="The Cultural Transmission Experiment",
            description="Investigates norm diffusion, cultural entropy shifts, and inter-community cultural divergence.",
            seed=212,
            population_size=120,
            duration_ticks=350,
            initial_resource_richness=1.05,
            scarcity=0.15,
            cultural_transmission_rate=0.60,
            social_learning_prob=0.45,
            social_interaction_prob=0.92,
            personality_means={"openness": 0.66, "conscientiousness": 0.52, "extraversion": 0.64, "agreeableness": 0.58, "emotional_stability": 0.55},
        ),
    },
    "trust_experiment": {
        "scenario_id": "trust_experiment",
        "title": "4. The Trust Experiment",
        "research_question": "How does asymmetric trust updating (fast decay on defection) sort social networks into high-trust clusters vs rivalries?",
        "config": ExperimentConfig(
            scenario_id="trust_experiment",
            name="The Trust Experiment",
            description="Studies dynamic interpersonal trust, reputation sorting, and network polarization.",
            seed=307,
            population_size=100,
            duration_ticks=300,
            initial_resource_richness=0.90,
            scarcity=0.32,
            cooperation_reward=0.25,
            social_interaction_prob=0.95,
            learning_rate=0.20,
            personality_means={"openness": 0.50, "conscientiousness": 0.54, "extraversion": 0.60, "agreeableness": 0.50, "emotional_stability": 0.52},
            personality_std=0.24,
        ),
    },
    "artificial_economy": {
        "scenario_id": "artificial_economy",
        "title": "5. The Artificial Economy",
        "research_question": "How do regional resource asymmetries drive tool crafting, bilateral trade volume, price discovery, and wealth Gini?",
        "config": ExperimentConfig(
            scenario_id="artificial_economy",
            name="The Artificial Economy",
            description="Examines production, bilateral resource exchange, scarcity pricing, and wealth stratification.",
            seed=415,
            population_size=120,
            duration_ticks=350,
            initial_resource_richness=0.95,
            scarcity=0.28,
            cooperation_reward=0.22,
            social_interaction_prob=0.88,
            learning_rate=0.18,
            personality_means={"openness": 0.52, "conscientiousness": 0.68, "extraversion": 0.62, "agreeableness": 0.52, "emotional_stability": 0.58},
        ),
    },
    "institutional_formation": {
        "scenario_id": "institutional_formation",
        "title": "6. The Institutional Formation Experiment",
        "research_question": "When do repeated trusted interactions crystallize into rule-enforcing pools, councils, guilds, and academies?",
        "config": ExperimentConfig(
            scenario_id="institutional_formation",
            name="The Institutional Formation Experiment",
            description="Investigates emergent governance structures, treasury redistribution, compliance, and institutional stability.",
            seed=521,
            population_size=110,
            duration_ticks=350,
            initial_resource_richness=1.0,
            scarcity=0.22,
            cooperation_reward=0.34,
            institutions_enabled=True,
            institution_formation_threshold=0.53,
            social_interaction_prob=0.92,
            personality_means={"openness": 0.56, "conscientiousness": 0.64, "extraversion": 0.58, "agreeableness": 0.64, "emotional_stability": 0.60},
        ),
    },
    "migration_experiment": {
        "scenario_id": "migration_experiment",
        "title": "7. The Migration Experiment",
        "research_question": "How do environmental shocks and regional depletion drive spatial migration and settlement concentration?",
        "config": ExperimentConfig(
            scenario_id="migration_experiment",
            name="The Migration Experiment",
            description="Studies spatial mobility, hazard avoidance, and settlement redistribution under climate shocks.",
            seed=633,
            population_size=100,
            duration_ticks=300,
            initial_resource_richness=0.85,
            scarcity=0.40,
            climate_severity=0.48,
            env_event_probability=0.14,
            exploration_rate=0.18,
            personality_means={"openness": 0.72, "conscientiousness": 0.50, "extraversion": 0.52, "agreeableness": 0.54, "emotional_stability": 0.45},
        ),
    },
    "collective_intelligence": {
        "scenario_id": "collective_intelligence",
        "title": "8. The Collective Intelligence Experiment",
        "research_question": "How does distributed communication and social learning aggregate knowledge and raise group decision quality?",
        "config": ExperimentConfig(
            scenario_id="collective_intelligence",
            name="The Collective Intelligence Experiment",
            description="Investigates information aggregation, belief convergence, and social learning performance.",
            seed=744,
            population_size=120,
            duration_ticks=350,
            initial_resource_richness=1.1,
            scarcity=0.12,
            learning_rate=0.22,
            social_learning_prob=0.50,
            cultural_transmission_rate=0.45,
            cooperation_reward=0.32,
            personality_means={"openness": 0.74, "conscientiousness": 0.62, "extraversion": 0.65, "agreeableness": 0.62, "emotional_stability": 0.60},
        ),
    },
}


def list_scenarios() -> list[dict[str, Any]]:
    return [
        {
            "scenario_id": item["scenario_id"],
            "title": item["title"],
            "research_question": item["research_question"],
            "config": item["config"].to_dict(),
        }
        for item in SCENARIO_DEFINITIONS.values()
    ]


def get_scenario_config(scenario_id: str) -> ExperimentConfig:
    if scenario_id not in SCENARIO_DEFINITIONS:
        raise KeyError(f"Unknown scenario: {scenario_id}")
    return ExperimentConfig.from_dict(SCENARIO_DEFINITIONS[scenario_id]["config"].to_dict())
