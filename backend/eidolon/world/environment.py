"""Environmental dynamics: seasonal cycles, resource regeneration, and natural events.

Simplified Modeling Assumptions:
1. Seasonal multipliers apply uniformly to resource regeneration rates across regions,
   modulated by each location's static fertility parameter.
2. Natural events (drought, bounty, storm, mineral_surge) affect a single region or
   location for instantaneous delta + short-lived hazard modulation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from eidolon.core.clock import SimulationClock
from eidolon.core.rng import SeededRNG
from eidolon.world.grid import WorldGrid

SEASON_REGEN_MULTIPLIERS: dict[str, dict[str, float]] = {
    "spring": {"food": 1.30, "water": 1.35, "raw_materials": 1.00, "tools": 1.00, "knowledge": 1.05, "energy": 1.05},
    "summer": {"food": 1.15, "water": 0.90, "raw_materials": 1.15, "tools": 1.00, "knowledge": 1.05, "energy": 1.35},
    "autumn": {"food": 1.40, "water": 1.05, "raw_materials": 1.10, "tools": 1.05, "knowledge": 1.10, "energy": 0.95},
    "winter": {"food": 0.45, "water": 0.80, "raw_materials": 0.85, "tools": 0.95, "knowledge": 1.15, "energy": 0.70},
}

SEASON_METABOLIC_MULTIPLIER: dict[str, float] = {
    "spring": 1.0,
    "summer": 1.05,
    "autumn": 1.0,
    "winter": 1.32,
}


@dataclass
class EnvironmentState:
    """Tracks active environmental conditions and cumulative natural event stats."""

    climate_severity: float = 0.0  # 0.0 mild -> 1.0 harsh
    regeneration_scale: float = 1.0
    event_probability: float = 0.04
    last_event_summary: str = "Stable"
    total_natural_events: int = 0

    def step(
        self,
        world: WorldGrid,
        clock: SimulationClock,
        rng: SeededRNG,
    ) -> list[dict[str, Any]]:
        """Regenerate world resources and optionally trigger a stochastic environmental event."""
        season = clock.season
        season_mults = SEASON_REGEN_MULTIPLIERS[season]
        severity_penalty = max(0.35, 1.0 - 0.55 * self.climate_severity)

        for loc in world.locations.values():
            for r_type, stock in loc.resources.items():
                mult = self.regeneration_scale * season_mults.get(r_type, 1.0) * severity_penalty
                stock.regenerate(multiplier=mult)

        emitted: list[dict[str, Any]] = []
        if rng.random() < self.event_probability:
            loc_ids = sorted(world.locations.keys())
            loc = world.locations[rng.choice(loc_ids)]
            evt_kind = rng.choice(["drought", "bounty", "storm", "mineral_discovery"])
            if evt_kind == "drought":
                if "water" in loc.resources:
                    loc.resources["water"].withdraw(loc.resources["water"].quantity * 0.30)
                if "food" in loc.resources:
                    loc.resources["food"].withdraw(loc.resources["food"].quantity * 0.22)
                self.last_event_summary = f"Drought in {loc.name}"
            elif evt_kind == "bounty":
                if "food" in loc.resources:
                    loc.resources["food"].deposit(loc.resources["food"].max_capacity * 0.25)
                if "water" in loc.resources:
                    loc.resources["water"].deposit(loc.resources["water"].max_capacity * 0.15)
                self.last_event_summary = f"Harvest bounty in {loc.name}"
            elif evt_kind == "storm":
                if "energy" in loc.resources:
                    loc.resources["energy"].withdraw(loc.resources["energy"].quantity * 0.20)
                loc.hazard_level = min(0.60, loc.hazard_level + 0.05)
                self.last_event_summary = f"Storm struck {loc.name}"
            else:
                if "raw_materials" in loc.resources:
                    loc.resources["raw_materials"].deposit(loc.resources["raw_materials"].max_capacity * 0.25)
                self.last_event_summary = f"Material vein found at {loc.name}"

            self.total_natural_events += 1
            emitted.append(
                {
                    "event_type": f"env_{evt_kind}",
                    "location_id": loc.location_id,
                    "location_name": loc.name,
                    "season": season,
                    "summary": self.last_event_summary,
                }
            )
        return emitted

    def to_dict(self) -> dict[str, Any]:
        return {
            "climate_severity": self.climate_severity,
            "regeneration_scale": self.regeneration_scale,
            "event_probability": self.event_probability,
            "last_event_summary": self.last_event_summary,
            "total_natural_events": self.total_natural_events,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EnvironmentState:
        return cls(
            climate_severity=float(data.get("climate_severity", 0.0)),
            regeneration_scale=float(data.get("regeneration_scale", 1.0)),
            event_probability=float(data.get("event_probability", 0.04)),
            last_event_summary=str(data.get("last_event_summary", "Stable")),
            total_natural_events=int(data.get("total_natural_events", 0)),
        )
