"""Graph-based 2D artificial world with regions, settlements, resource nodes, and transport edges."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Any

from eidolon.core.rng import SeededRNG
from eidolon.world.resources import RESOURCE_TYPES, ResourceStock


@dataclass
class Location:
    """A node in the world graph (settlement, resource deposit, market hub, or sanctuary)."""

    location_id: str
    name: str
    region: str
    kind: str  # settlement | resource_node | market | sanctuary | outpost
    x: float
    y: float
    fertility: float
    hazard_level: float
    capacity: int
    neighbors: list[str] = field(default_factory=list)
    resources: dict[str, ResourceStock] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "location_id": self.location_id,
            "name": self.name,
            "region": self.region,
            "kind": self.kind,
            "x": round(self.x, 3),
            "y": round(self.y, 3),
            "fertility": round(self.fertility, 3),
            "hazard_level": round(self.hazard_level, 3),
            "capacity": self.capacity,
            "neighbors": list(self.neighbors),
            "resources": {k: v.to_dict() for k, v in self.resources.items()},
        }

    def to_snapshot_dict(self) -> dict[str, Any]:
        return {
            "location_id": self.location_id,
            "name": self.name,
            "region": self.region,
            "kind": self.kind,
            "x": self.x,
            "y": self.y,
            "fertility": self.fertility,
            "hazard_level": self.hazard_level,
            "capacity": self.capacity,
            "neighbors": list(self.neighbors),
            "resources": {k: v.to_snapshot_dict() for k, v in self.resources.items()},
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Location:
        return cls(
            location_id=data["location_id"],
            name=data["name"],
            region=data["region"],
            kind=data["kind"],
            x=float(data["x"]),
            y=float(data["y"]),
            fertility=float(data["fertility"]),
            hazard_level=float(data["hazard_level"]),
            capacity=int(data["capacity"]),
            neighbors=list(data.get("neighbors", [])),
            resources={
                k: ResourceStock.from_dict(v)
                for k, v in data.get("resources", {}).items()
            },
        )


class WorldGrid:
    """Graph-based spatial world supporting pathfinding, regional queries, and resource stocks."""

    def __init__(self, locations: dict[str, Location] | None = None) -> None:
        self.locations: dict[str, Location] = locations or {}
        self._shortest_next_hop: dict[tuple[str, str], str] = {}
        if self.locations:
            self._rebuild_routing()

    def _rebuild_routing(self) -> None:
        self._shortest_next_hop.clear()
        for src in self.locations:
            queue: deque[str] = deque([src])
            parent: dict[str, str | None] = {src: None}
            while queue:
                curr = queue.popleft()
                for nxt in self.locations[curr].neighbors:
                    if nxt not in parent and nxt in self.locations:
                        parent[nxt] = curr
                        queue.append(nxt)
            for dst in parent:
                if dst == src:
                    continue
                step = dst
                while parent[step] is not None and parent[step] != src:
                    step = parent[step]  # type: ignore[assignment]
                if parent[step] == src:
                    self._shortest_next_hop[(src, dst)] = step

    def next_hop(self, src_id: str, dst_id: str) -> str:
        if src_id == dst_id:
            return src_id
        return self._shortest_next_hop.get((src_id, dst_id), src_id)

    def distance(self, loc_a: str, loc_b: str) -> float:
        a = self.locations[loc_a]
        b = self.locations[loc_b]
        return ((a.x - b.x) ** 2 + (a.y - b.y) ** 2) ** 0.5

    def total_resources(self) -> dict[str, float]:
        totals = {r: 0.0 for r in RESOURCE_TYPES}
        for loc in self.locations.values():
            for r, stock in loc.resources.items():
                totals[r] += stock.quantity
        return totals

    def to_dict(self) -> dict[str, Any]:
        return {"locations": {k: v.to_dict() for k, v in self.locations.items()}}

    def to_snapshot_dict(self) -> dict[str, Any]:
        return {"locations": {k: v.to_snapshot_dict() for k, v in self.locations.items()}}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WorldGrid:
        locs = {k: Location.from_dict(v) for k, v in data["locations"].items()}
        return cls(locations=locs)

    @classmethod
    def generate(
        cls,
        rng: SeededRNG,
        num_locations: int = 16,
        resource_richness: float = 1.0,
        scarcity: float = 0.0,
    ) -> WorldGrid:
        """Creates a multi-region connected world graph with settlements, resource nodes, and markets."""
        regions = [
            ("Central Plains", 50.0, 50.0),
            ("River Basin", 26.0, 62.0),
            ("Northern Highlands", 48.0, 84.0),
            ("Eastern Forest", 78.0, 52.0),
            ("Southern Oasis", 52.0, 18.0),
        ]
        templates = [
            ("Central Commons", "Central Plains", "settlement", 50.0, 50.0, 0.75, 0.05),
            ("Grand Bazaar", "Central Plains", "market", 58.0, 46.0, 0.55, 0.08),
            ("Atrium Archive", "Central Plains", "sanctuary", 42.0, 48.0, 0.60, 0.04),
            ("Verdant Bend", "River Basin", "settlement", 28.0, 60.0, 0.90, 0.06),
            ("Clearwater Spring", "River Basin", "resource_node", 18.0, 70.0, 0.95, 0.07),
            ("Reed Granary", "River Basin", "resource_node", 24.0, 44.0, 0.85, 0.06),
            ("Granite Ridge", "Northern Highlands", "resource_node", 46.0, 86.0, 0.35, 0.16),
            ("Windspire Bastion", "Northern Highlands", "outpost", 60.0, 80.0, 0.40, 0.14),
            ("Solar Terrace", "Northern Highlands", "resource_node", 32.0, 82.0, 0.45, 0.12),
            ("Timber Reach", "Eastern Forest", "resource_node", 78.0, 58.0, 0.72, 0.10),
            ("Sylvan Haven", "Eastern Forest", "settlement", 74.0, 42.0, 0.80, 0.07),
            ("Forge Hollow", "Eastern Forest", "market", 86.0, 48.0, 0.50, 0.11),
            ("Dune Well", "Southern Oasis", "resource_node", 50.0, 16.0, 0.55, 0.14),
            ("Sunstone Camp", "Southern Oasis", "settlement", 62.0, 22.0, 0.62, 0.11),
            ("Amber Quarry", "Southern Oasis", "resource_node", 36.0, 20.0, 0.40, 0.15),
            ("Crossroads Gate", "Central Plains", "outpost", 46.0, 32.0, 0.60, 0.09),
        ]

        selected = templates[: max(6, min(num_locations, len(templates)))]
        effective_mult = max(0.15, resource_richness * (1.0 - 0.75 * scarcity))

        locations: dict[str, Location] = {}
        for idx, (name, region, kind, bx, by, fertility, hazard) in enumerate(selected):
            loc_id = f"loc_{idx:02d}"
            jx = max(5.0, min(95.0, bx + rng.uniform(-3.0, 3.0)))
            jy = max(5.0, min(95.0, by + rng.uniform(-3.0, 3.0)))

            # Resource profile depends on location kind and region
            stocks: dict[str, ResourceStock] = {}
            for r in RESOURCE_TYPES:
                base_cap = 120.0 * effective_mult
                regen = 2.2 * fertility * effective_mult
                if r == "food":
                    if "Basin" in region or "Forest" in region or kind == "settlement":
                        base_cap *= 1.6
                        regen *= 1.5
                elif r == "water":
                    if "Basin" in region or "Oasis" in region:
                        base_cap *= 1.8
                        regen *= 1.7
                elif r == "raw_materials":
                    if "Highlands" in region or "Forest" in region or "Quarry" in name:
                        base_cap *= 1.7
                        regen *= 1.4
                elif r == "energy":
                    if "Highlands" in region or "Oasis" in region:
                        base_cap *= 1.5
                        regen *= 1.5
                elif r == "tools":
                    base_cap = (55.0 if kind in ("market", "settlement") else 25.0) * effective_mult
                    regen = (0.35 if kind == "market" else 0.10) * effective_mult
                elif r == "knowledge":
                    base_cap = (70.0 if kind in ("sanctuary", "settlement") else 30.0) * effective_mult
                    regen = (0.55 if kind == "sanctuary" else 0.18) * effective_mult

                init_qty = base_cap * rng.uniform(0.55, 0.92)
                stocks[r] = ResourceStock(
                    resource_type=r,
                    quantity=init_qty,
                    max_capacity=base_cap,
                    regen_rate=regen,
                )

            locations[loc_id] = Location(
                location_id=loc_id,
                name=name,
                region=region,
                kind=kind,
                x=jx,
                y=jy,
                fertility=fertility,
                hazard_level=hazard,
                capacity=400,
                resources=stocks,
            )

        # Build connected transport network: MST + 2 nearest extra edges per node
        ids = list(locations.keys())
        connected = {ids[0]}
        unconnected = set(ids[1:])

        def dist(a: str, b: str) -> float:
            la, lb = locations[a], locations[b]
            return ((la.x - lb.x) ** 2 + (la.y - lb.y) ** 2) ** 0.5

        while unconnected:
            best_pair = None
            best_d = 1e9
            for u in connected:
                for v in unconnected:
                    d = dist(u, v)
                    if d < best_d:
                        best_d = d
                        best_pair = (u, v)
            assert best_pair is not None
            u, v = best_pair
            locations[u].neighbors.append(v)
            locations[v].neighbors.append(u)
            connected.add(v)
            unconnected.remove(v)

        # Add redundancy loops for realistic migration & trade paths
        for u in ids:
            nearest = sorted((v for v in ids if v != u), key=lambda v: dist(u, v))
            for v in nearest[:3]:
                if v not in locations[u].neighbors:
                    locations[u].neighbors.append(v)
                if u not in locations[v].neighbors:
                    locations[v].neighbors.append(u)

        return cls(locations=locations)
