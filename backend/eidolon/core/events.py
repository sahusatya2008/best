"""Structured event system for traceability, replay, and analytics."""

from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class SimulationEvent:
    """Represents a verifiable state-changing event within EIDOLON."""

    tick: int
    event_type: str
    actor_id: str | None = None
    target_id: str | None = None
    location_id: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    explanation: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class EventBus:
    """Bounded in-memory event buffer with pending persistence queue."""

    def __init__(self, max_recent: int = 2000) -> None:
        self.recent: deque[SimulationEvent] = deque(maxlen=max_recent)
        self.pending_persist: list[SimulationEvent] = []
        self.total_emitted: int = 0

    def emit(self, event: SimulationEvent) -> None:
        self.recent.append(event)
        self.pending_persist.append(event)
        self.total_emitted += 1

    def drain_pending(self) -> list[SimulationEvent]:
        items = self.pending_persist
        self.pending_persist = []
        return items

    def for_agent(self, agent_id: str, limit: int = 50) -> list[dict[str, Any]]:
        matches = [
            e.to_dict()
            for e in reversed(self.recent)
            if e.actor_id == agent_id or e.target_id == agent_id
        ]
        return matches[:limit]

    def recent_list(self, limit: int = 100, event_type: str | None = None) -> list[dict[str, Any]]:
        out = []
        for e in reversed(self.recent):
            if event_type and e.event_type != event_type:
                continue
            out.append(e.to_dict())
            if len(out) >= limit:
                break
        return out
