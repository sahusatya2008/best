"""Original local learning engine: tabular Q-learning, social learning, and failure adaptation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

ACTIONS: tuple[str, ...] = (
    "harvest_food",
    "gather_water",
    "extract_materials",
    "craft_tools",
    "research_knowledge",
    "cooperate",
    "trade",
    "compete",
    "communicate",
    "migrate",
    "rest",
)


@dataclass
class LearningConfig:
    learning_rate: float = 0.15       # alpha
    discount_factor: float = 0.90     # gamma
    exploration_rate: float = 0.12    # epsilon
    social_learning_prob: float = 0.25
    adaptation_speed: float = 1.0
    memory_capacity: int = 80


@dataclass
class LearningUpdateRecord:
    tick: int
    state_key: str
    action: str
    q_value: float
    reward: float
    next_state_key: str
    td_error: float
    source: str  # q_learning | social_learning | failure_adaptation

    def to_dict(self) -> dict[str, Any]:
        return {
            "tick": self.tick,
            "state_key": self.state_key,
            "action": self.action,
            "q_value": round(self.q_value, 4),
            "reward": round(self.reward, 4),
            "next_state_key": self.next_state_key,
            "td_error": round(self.td_error, 4),
            "source": self.source,
        }


class QLearningEngine:
    """Tabular Q-learning + social observation learning + failure avoidance."""

    def __init__(self) -> None:
        # q_table[state_key][action] -> float
        self.q_table: dict[str, dict[str, float]] = {}
        self.failure_counts: dict[str, int] = {}
        self.total_updates: int = 0
        self.social_adoptions: int = 0
        self.recent_records: list[LearningUpdateRecord] = []

    def _ensure_state(self, state_key: str) -> dict[str, float]:
        row = self.q_table.get(state_key)
        if row is None:
            row = {a: 0.0 for a in ACTIONS}
            self.q_table[state_key] = row
        return row

    def get_q(self, state_key: str, action: str) -> float:
        return self.q_table.get(state_key, {}).get(action, 0.0)

    def max_q(self, state_key: str) -> float:
        row = self.q_table.get(state_key)
        if not row:
            return 0.0
        return max(row.values())

    def update(
        self,
        tick: int,
        state_key: str,
        action: str,
        reward: float,
        next_state_key: str,
        cfg: LearningConfig,
    ) -> LearningUpdateRecord:
        """Standard tabular Q-learning update: Q(s,a) <- Q(s,a) + alpha[r + gamma*max Q(s',a') - Q(s,a)]."""
        row = self._ensure_state(state_key)
        old_q = row.get(action, 0.0)
        next_max = self.max_q(next_state_key)
        alpha = max(0.01, min(0.95, cfg.learning_rate * cfg.adaptation_speed))
        # Prevent failed self-loop actions from borrowing positive Q-value from sibling actions
        if reward < 0.0 and next_state_key == state_key:
            td_target = reward
        else:
            td_target = reward + cfg.discount_factor * next_max
        td_error = td_target - old_q
        new_q = old_q + alpha * td_error
        row[action] = max(-5.0, min(5.0, new_q))

        source = "q_learning"
        if reward < -0.05:
            self.failure_counts[action] = self.failure_counts.get(action, 0) + 1
            source = "failure_adaptation"
        elif reward > 0.05 and self.failure_counts.get(action, 0) > 0:
            self.failure_counts[action] = max(0, self.failure_counts[action] - 1)

        self.total_updates += 1
        rec = LearningUpdateRecord(
            tick=tick,
            state_key=state_key,
            action=action,
            q_value=row[action],
            reward=reward,
            next_state_key=next_state_key,
            td_error=td_error,
            source=source,
        )
        self.recent_records.append(rec)
        if len(self.recent_records) > 30:
            self.recent_records.pop(0)
        return rec

    def social_learn(
        self,
        tick: int,
        state_key: str,
        observed_action: str,
        observed_reward: float,
        trust_in_model: float,
        cfg: LearningConfig,
    ) -> LearningUpdateRecord | None:
        """Adopt a successful strategy observed from a trusted peer."""
        if observed_reward <= 0.05 or observed_action not in ACTIONS:
            return None
        row = self._ensure_state(state_key)
        old_q = row.get(observed_action, 0.0)
        social_alpha = max(0.02, min(0.5, cfg.learning_rate * (0.4 + 0.6 * trust_in_model)))
        td_error = observed_reward - old_q
        new_q = old_q + social_alpha * td_error
        row[observed_action] = max(-5.0, min(5.0, new_q))
        self.social_adoptions += 1
        self.total_updates += 1
        rec = LearningUpdateRecord(
            tick=tick,
            state_key=state_key,
            action=observed_action,
            q_value=row[observed_action],
            reward=observed_reward,
            next_state_key=state_key,
            td_error=td_error,
            source="social_learning",
        )
        self.recent_records.append(rec)
        if len(self.recent_records) > 30:
            self.recent_records.pop(0)
        return rec

    def mean_q_value(self) -> float:
        if not self.q_table:
            return 0.0
        vals = [v for row in self.q_table.values() for v in row.values()]
        return sum(vals) / len(vals) if vals else 0.0

    def failure_penalty(self, action: str) -> float:
        cnt = self.failure_counts.get(action, 0)
        return min(0.45, cnt * 0.08)

    def to_dict(self) -> dict[str, Any]:
        return {
            "q_table": {s: {a: round(v, 5) for a, v in row.items()} for s, row in self.q_table.items()},
            "failure_counts": dict(self.failure_counts),
            "total_updates": self.total_updates,
            "social_adoptions": self.social_adoptions,
            "recent_records": [r.to_dict() for r in self.recent_records],
        }

    def to_snapshot_dict(self) -> dict[str, Any]:
        return {
            "q_table": {s: dict(row) for s, row in self.q_table.items()},
            "failure_counts": dict(self.failure_counts),
            "total_updates": self.total_updates,
            "social_adoptions": self.social_adoptions,
            "recent_records": [
                {
                    "tick": r.tick,
                    "state_key": r.state_key,
                    "action": r.action,
                    "q_value": r.q_value,
                    "reward": r.reward,
                    "next_state_key": r.next_state_key,
                    "td_error": r.td_error,
                    "source": r.source,
                }
                for r in self.recent_records
            ],
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> QLearningEngine:
        eng = cls()
        eng.q_table = {
            s: {a: float(v) for a, v in row.items()}
            for s, row in d.get("q_table", {}).items()
        }
        eng.failure_counts = {k: int(v) for k, v in d.get("failure_counts", {}).items()}
        eng.total_updates = int(d.get("total_updates", 0))
        eng.social_adoptions = int(d.get("social_adoptions", 0))
        eng.recent_records = [
            LearningUpdateRecord(**r) for r in d.get("recent_records", [])
        ]
        return eng
