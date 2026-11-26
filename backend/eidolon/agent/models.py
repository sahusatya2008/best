"""Agent Cognitive Architecture (ACA) data models: identity, Big Five personality, needs, beliefs, goals."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Any

from eidolon.core.rng import SeededRNG
from eidolon.world.resources import RESOURCE_TYPES, empty_inventory

OCCUPATIONS: tuple[str, ...] = (
    "forager",
    "artisan",
    "scholar",
    "trader",
    "coordinator",
    "explorer",
)

NEED_NAMES: tuple[str, ...] = (
    "nutrition",
    "energy",
    "safety",
    "social_connection",
    "belonging",
    "achievement",
    "knowledge_acquisition",
    "resource_security",
)


@dataclass
class BigFiveTraits:
    """Five-factor personality model in [0.0, 1.0]."""

    openness: float = 0.5
    conscientiousness: float = 0.5
    extraversion: float = 0.5
    agreeableness: float = 0.5
    emotional_stability: float = 0.5

    def to_dict(self) -> dict[str, float]:
        return {
            "openness": round(self.openness, 4),
            "conscientiousness": round(self.conscientiousness, 4),
            "extraversion": round(self.extraversion, 4),
            "agreeableness": round(self.agreeableness, 4),
            "emotional_stability": round(self.emotional_stability, 4),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> BigFiveTraits:
        return cls(
            openness=float(d["openness"]),
            conscientiousness=float(d["conscientiousness"]),
            extraversion=float(d["extraversion"]),
            agreeableness=float(d["agreeableness"]),
            emotional_stability=float(d["emotional_stability"]),
        )


@dataclass
class AgentNeeds:
    """Eight normalized internal needs in [0.0, 1.0], where 1.0 = fully satisfied."""

    nutrition: float = 0.78
    energy: float = 0.80
    safety: float = 0.78
    social_connection: float = 0.65
    belonging: float = 0.60
    achievement: float = 0.55
    knowledge_acquisition: float = 0.55
    resource_security: float = 0.62

    def clamp_all(self) -> None:
        for name in NEED_NAMES:
            val = getattr(self, name)
            setattr(self, name, max(0.0, min(1.0, float(val))))

    def get(self, name: str) -> float:
        return float(getattr(self, name))

    def adjust(self, name: str, delta: float) -> float:
        curr = float(getattr(self, name))
        nxt = max(0.0, min(1.0, curr + delta))
        setattr(self, name, nxt)
        return nxt - curr

    def most_urgent(self) -> tuple[str, float]:
        best_name = NEED_NAMES[0]
        best_urg = -1.0
        for name in NEED_NAMES:
            urg = 1.0 - float(getattr(self, name))
            if urg > best_urg:
                best_urg = urg
                best_name = name
        return best_name, best_urg

    def mean_satisfaction(self) -> float:
        return sum(float(getattr(self, n)) for n in NEED_NAMES) / len(NEED_NAMES)

    def to_dict(self) -> dict[str, float]:
        return {n: round(float(getattr(self, n)), 4) for n in NEED_NAMES}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> AgentNeeds:
        return cls(**{n: float(d.get(n, 0.6)) for n in NEED_NAMES})


@dataclass
class AgentGoal:
    goal_id: str
    goal_type: str  # survive | prosper | belong | learn | cooperate | lead | explore
    target_value: float
    priority: float
    progress: float = 0.0
    active: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "goal_id": self.goal_id,
            "goal_type": self.goal_type,
            "target_value": round(self.target_value, 4),
            "priority": round(self.priority, 4),
            "progress": round(self.progress, 4),
            "active": self.active,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> AgentGoal:
        return cls(
            goal_id=d["goal_id"],
            goal_type=d["goal_type"],
            target_value=float(d["target_value"]),
            priority=float(d["priority"]),
            progress=float(d.get("progress", 0.0)),
            active=bool(d.get("active", True)),
        )


@dataclass
class AgentBelief:
    belief_key: str
    value: float
    confidence: float
    updated_tick: int

    def update(self, evidence: float, tick: int, weight: float = 0.25) -> None:
        eff_w = max(0.05, min(0.8, weight * (1.2 - 0.5 * self.confidence)))
        self.value = max(0.0, min(1.0, (1.0 - eff_w) * self.value + eff_w * evidence))
        self.confidence = min(1.0, self.confidence + 0.04)
        self.updated_tick = tick

    def to_dict(self) -> dict[str, Any]:
        return {
            "belief_key": self.belief_key,
            "value": round(self.value, 4),
            "confidence": round(self.confidence, 4),
            "updated_tick": self.updated_tick,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> AgentBelief:
        return cls(
            belief_key=d["belief_key"],
            value=float(d["value"]),
            confidence=float(d["confidence"]),
            updated_tick=int(d["updated_tick"]),
        )


DEFAULT_CULTURAL_TRAITS: dict[str, str] = {
    "sharing_norm": "balanced",       # generous | balanced | hoarding
    "work_ethic": "industrious",      # industrious | collaborative | exploratory
    "conflict_style": "diplomatic",   # diplomatic | assertive | avoidant
    "governance_pref": "council",     # council | market | autonomous
}


def generate_agent_name(idx: int, rng: SeededRNG) -> str:
    syllables_a = ("Ae", "Ka", "Ly", "Or", "Va", "Th", "Si", "El", "No", "Za", "Cy", "Mi")
    syllables_b = ("lon", "ris", "ven", "dor", "ra", "mus", "thia", "kel", "phor", "nix", "len", "ta")
    return f"{rng.choice(syllables_a)}{rng.choice(syllables_b)}-{idx:03d}"
