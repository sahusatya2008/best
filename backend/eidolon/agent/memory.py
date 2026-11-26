"""Multi-layered local memory architecture: Working, Episodic, Semantic, and Procedural memory."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass
class MemoryEntry:
    """A structured memory item stored across cognitive layers."""

    tick: int
    layer: str  # working | episodic | semantic | procedural
    event_type: str
    participants: list[str]
    context: dict[str, float | str]
    outcome: float
    emotional_significance: float
    relevance_weight: float = 1.0
    recall_count: int = 0
    consolidated: bool = False

    def feature_vector(self) -> np.ndarray:
        """Deterministic 5D local feature vector for similarity retrieval (no external embeddings)."""
        return np.array(
            [
                float(self.context.get("need_urgency", 0.5)),
                float(self.context.get("scarcity", 0.5)),
                float(self.context.get("social_density", 0.5)),
                float(self.context.get("safety", 0.5)),
                max(-1.0, min(1.0, float(self.outcome))),
            ],
            dtype=np.float64,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "tick": self.tick,
            "layer": self.layer,
            "event_type": self.event_type,
            "participants": list(self.participants),
            "context": dict(self.context),
            "outcome": round(self.outcome, 4),
            "emotional_significance": round(self.emotional_significance, 4),
            "relevance_weight": round(self.relevance_weight, 4),
            "recall_count": self.recall_count,
            "consolidated": self.consolidated,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> MemoryEntry:
        return cls(
            tick=int(d["tick"]),
            layer=d["layer"],
            event_type=d["event_type"],
            participants=list(d.get("participants", [])),
            context=dict(d.get("context", {})),
            outcome=float(d["outcome"]),
            emotional_significance=float(d["emotional_significance"]),
            relevance_weight=float(d.get("relevance_weight", 1.0)),
            recall_count=int(d.get("recall_count", 0)),
            consolidated=bool(d.get("consolidated", False)),
        )


@dataclass
class ProceduralStrategy:
    """Learned action-outcome statistics stored in procedural memory."""

    action: str
    successes: int = 0
    failures: int = 0
    avg_outcome: float = 0.0
    last_tick: int = 0

    def record(self, outcome: float, tick: int) -> None:
        total = self.successes + self.failures
        self.avg_outcome = (self.avg_outcome * total + outcome) / (total + 1)
        if outcome >= 0.0:
            self.successes += 1
        else:
            self.failures += 1
        self.last_tick = tick

    @property
    def success_rate(self) -> float:
        total = self.successes + self.failures
        if total == 0:
            return 0.5
        return self.successes / total

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "successes": self.successes,
            "failures": self.failures,
            "avg_outcome": round(self.avg_outcome, 4),
            "last_tick": self.last_tick,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> ProceduralStrategy:
        return cls(
            action=d["action"],
            successes=int(d.get("successes", 0)),
            failures=int(d.get("failures", 0)),
            avg_outcome=float(d.get("avg_outcome", 0.0)),
            last_tick=int(d.get("last_tick", 0)),
        )


class AgentMemory:
    """Bounded 4-layer cognitive memory with similarity retrieval and periodic consolidation."""

    def __init__(self, episodic_capacity: int = 80, working_capacity: int = 8) -> None:
        self.episodic_capacity = max(16, int(episodic_capacity))
        self.working_capacity = max(4, int(working_capacity))
        self.working: deque[MemoryEntry] = deque(maxlen=self.working_capacity)
        self.episodic: list[MemoryEntry] = []
        self.semantic: dict[str, dict[str, Any]] = {}
        self.procedural: dict[str, ProceduralStrategy] = {}

    def record_experience(self, entry: MemoryEntry) -> None:
        """Store into working memory, episodic memory, and update procedural trace."""
        w_entry = MemoryEntry(
            tick=entry.tick,
            layer="working",
            event_type=entry.event_type,
            participants=list(entry.participants),
            context=dict(entry.context),
            outcome=entry.outcome,
            emotional_significance=entry.emotional_significance,
            relevance_weight=entry.relevance_weight,
        )
        self.working.append(w_entry)

        ep = MemoryEntry(
            tick=entry.tick,
            layer="episodic",
            event_type=entry.event_type,
            participants=list(entry.participants),
            context=dict(entry.context),
            outcome=entry.outcome,
            emotional_significance=entry.emotional_significance,
            relevance_weight=entry.relevance_weight,
        )
        self.episodic.append(ep)
        if len(self.episodic) > self.episodic_capacity:
            # Evict lowest priority memory (combining relevance, emotional significance, and recency)
            self.episodic.sort(
                key=lambda m: (
                    m.emotional_significance * 0.45
                    + m.relevance_weight * 0.35
                    + (0.2 if m.consolidated else 0.0)
                    + m.tick * 0.0005
                ),
                reverse=True,
            )
            self.episodic = self.episodic[: self.episodic_capacity]

        strat = self.procedural.get(entry.event_type)
        if strat is None:
            strat = ProceduralStrategy(action=entry.event_type)
            self.procedural[entry.event_type] = strat
        strat.record(entry.outcome, entry.tick)

    def retrieve_similar(
        self,
        current_context: dict[str, float | str],
        current_tick: int,
        action_filter: str | None = None,
        top_k: int = 5,
    ) -> list[tuple[float, MemoryEntry]]:
        """Local mathematical cosine + contextual similarity retrieval over episodic memory."""
        if not self.episodic:
            return []

        query_vec = np.array(
            [
                float(current_context.get("need_urgency", 0.5)),
                float(current_context.get("scarcity", 0.5)),
                float(current_context.get("social_density", 0.5)),
                float(current_context.get("safety", 0.5)),
                0.5,
            ],
            dtype=np.float64,
        )
        q_norm = float(np.linalg.norm(query_vec)) or 1.0
        query_loc = current_context.get("location_id")

        scored: list[tuple[float, MemoryEntry]] = []
        for mem in self.episodic:
            if action_filter and mem.event_type != action_filter:
                continue
            m_vec = mem.feature_vector()
            m_norm = float(np.linalg.norm(m_vec)) or 1.0
            cos_sim = float(np.dot(query_vec, m_vec) / (q_norm * m_norm))
            loc_bonus = 0.18 if query_loc and mem.context.get("location_id") == query_loc else 0.0
            age = max(0, current_tick - mem.tick)
            recency = 1.0 / (1.0 + 0.015 * age)
            score = (
                0.45 * max(0.0, cos_sim)
                + loc_bonus
                + 0.20 * recency
                + 0.20 * mem.emotional_significance
                + 0.15 * mem.relevance_weight
            )
            scored.append((score, mem))

        scored.sort(key=lambda item: item[0], reverse=True)
        top = scored[:top_k]
        for _, mem in top:
            mem.recall_count += 1
        return top

    def update_semantic(self, key: str, value: Any, confidence: float, tick: int) -> None:
        existing = self.semantic.get(key)
        if existing and isinstance(value, (int, float)) and isinstance(existing.get("value"), (int, float)):
            alpha = 0.35
            blended = (1.0 - alpha) * float(existing["value"]) + alpha * float(value)
            self.semantic[key] = {
                "value": round(blended, 4),
                "confidence": round(min(1.0, max(confidence, float(existing.get("confidence", 0.5)))), 4),
                "updated_tick": tick,
            }
        else:
            self.semantic[key] = {
                "value": value,
                "confidence": round(min(1.0, max(0.0, confidence)), 4),
                "updated_tick": tick,
            }

    def consolidate(self, current_tick: int) -> int:
        """Extract recurring patterns into semantic memory and decay obsolete low-value traces."""
        if not self.episodic:
            return 0
        by_action: dict[str, list[MemoryEntry]] = {}
        for mem in self.episodic:
            by_action.setdefault(mem.event_type, []).append(mem)
            # Decay relevance slowly for un-recalled old memories
            age = max(0, current_tick - mem.tick)
            if age > 20 and mem.recall_count == 0 and mem.emotional_significance < 0.5:
                mem.relevance_weight = max(0.05, mem.relevance_weight * 0.90)

        patterns_extracted = 0
        for act, items in by_action.items():
            if len(items) >= 3:
                mean_out = sum(m.outcome for m in items) / len(items)
                self.update_semantic(
                    key=f"pattern.{act}.expected_outcome",
                    value=mean_out,
                    confidence=min(1.0, 0.4 + 0.1 * len(items)),
                    tick=current_tick,
                )
                for m in items:
                    if abs(m.outcome) >= 0.25 or m.emotional_significance >= 0.6:
                        m.consolidated = True
                patterns_extracted += 1
        return patterns_extracted

    def summary(self) -> dict[str, Any]:
        return {
            "working_count": len(self.working),
            "episodic_count": len(self.episodic),
            "semantic_count": len(self.semantic),
            "procedural_count": len(self.procedural),
            "recent_episodic": [m.to_dict() for m in self.episodic[-8:]],
            "semantic": dict(self.semantic),
            "procedural": {k: v.to_dict() for k, v in self.procedural.items()},
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "episodic_capacity": self.episodic_capacity,
            "working_capacity": self.working_capacity,
            "working": [m.to_dict() for m in self.working],
            "episodic": [m.to_dict() for m in self.episodic],
            "semantic": dict(self.semantic),
            "procedural": {k: v.to_dict() for k, v in self.procedural.items()},
        }

    def to_snapshot_dict(self) -> dict[str, Any]:
        def exact_entry(m: MemoryEntry) -> dict[str, Any]:
            return {
                "tick": m.tick,
                "layer": m.layer,
                "event_type": m.event_type,
                "participants": list(m.participants),
                "context": dict(m.context),
                "outcome": m.outcome,
                "emotional_significance": m.emotional_significance,
                "relevance_weight": m.relevance_weight,
                "recall_count": m.recall_count,
                "consolidated": m.consolidated,
            }

        return {
            "episodic_capacity": self.episodic_capacity,
            "working_capacity": self.working_capacity,
            "working": [exact_entry(m) for m in self.working],
            "episodic": [exact_entry(m) for m in self.episodic],
            "semantic": dict(self.semantic),
            "procedural": {
                k: {
                    "action": v.action,
                    "successes": v.successes,
                    "failures": v.failures,
                    "avg_outcome": v.avg_outcome,
                    "last_tick": v.last_tick,
                }
                for k, v in self.procedural.items()
            },
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> AgentMemory:
        mem = cls(
            episodic_capacity=int(d.get("episodic_capacity", 80)),
            working_capacity=int(d.get("working_capacity", 8)),
        )
        for item in d.get("working", []):
            mem.working.append(MemoryEntry.from_dict(item))
        mem.episodic = [MemoryEntry.from_dict(item) for item in d.get("episodic", [])]
        mem.semantic = dict(d.get("semantic", {}))
        mem.procedural = {
            k: ProceduralStrategy.from_dict(v)
            for k, v in d.get("procedural", {}).items()
        }
        return mem
