"""Deterministic simulation clock and calendar."""

from __future__ import annotations

from dataclasses import dataclass

SEASONS = ("spring", "summer", "autumn", "winter")


@dataclass
class SimulationClock:
    """Tracks discrete simulation ticks, days, seasons, and years."""

    tick: int = 0
    ticks_per_day: int = 4
    days_per_season: int = 15

    @property
    def day(self) -> int:
        return self.tick // self.ticks_per_day

    @property
    def season_index(self) -> int:
        return (self.day // self.days_per_season) % len(SEASONS)

    @property
    def season(self) -> str:
        return SEASONS[self.season_index]

    @property
    def year(self) -> int:
        return (self.day // (self.days_per_season * len(SEASONS))) + 1

    def advance(self) -> int:
        self.tick += 1
        return self.tick

    def to_dict(self) -> dict[str, int | str]:
        return {
            "tick": self.tick,
            "day": self.day,
            "season": self.season,
            "year": self.year,
            "ticks_per_day": self.ticks_per_day,
            "days_per_season": self.days_per_season,
        }

    @classmethod
    def from_dict(cls, data: dict) -> SimulationClock:
        return cls(
            tick=int(data["tick"]),
            ticks_per_day=int(data.get("ticks_per_day", 4)),
            days_per_season=int(data.get("days_per_season", 15)),
        )
