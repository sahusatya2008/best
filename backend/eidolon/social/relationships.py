"""Social network, weighted typed relationships, dynamic trust, reputation, and community detection."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import networkx as nx

RELATIONSHIP_TYPES: tuple[str, ...] = (
    "cooperation",
    "friendship",
    "rivalry",
    "family",
    "mentorship",
    "affiliation",
)


@dataclass
class RelationshipEdge:
    source_id: str
    target_id: str
    rel_type: str
    weight: float
    trust: float
    interaction_count: int = 1
    last_tick: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "rel_type": self.rel_type,
            "weight": round(self.weight, 4),
            "trust": round(self.trust, 4),
            "interaction_count": self.interaction_count,
            "last_tick": self.last_tick,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> RelationshipEdge:
        return cls(
            source_id=d["source_id"],
            target_id=d["target_id"],
            rel_type=d["rel_type"],
            weight=float(d["weight"]),
            trust=float(d["trust"]),
            interaction_count=int(d.get("interaction_count", 1)),
            last_tick=int(d.get("last_tick", 0)),
        )


@dataclass
class Community:
    community_id: str
    name: str
    founded_tick: int
    member_ids: list[str]
    cohesion: float
    centroid_x: float
    centroid_y: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "community_id": self.community_id,
            "name": self.name,
            "founded_tick": self.founded_tick,
            "member_ids": list(self.member_ids),
            "member_count": len(self.member_ids),
            "cohesion": round(self.cohesion, 4),
            "centroid_x": round(self.centroid_x, 3),
            "centroid_y": round(self.centroid_y, 3),
        }


class SocialNetwork:
    """Manages agent relationships, dynamic trust, reputation, and emergent communities."""

    def __init__(self) -> None:
        # edges[(a, b)] where a < b for undirected pair, storing primary RelationshipEdge
        self.edges: dict[tuple[str, str], RelationshipEdge] = {}
        # adjacency[agent_id][other_id] -> trust float (fast O(1) lookup)
        self.trust_map: dict[str, dict[str, float]] = {}
        self.communities: dict[str, Community] = {}

    @staticmethod
    def _pair(a: str, b: str) -> tuple[str, str]:
        return (a, b) if a < b else (b, a)

    def get_trust(self, a: str, b: str, default: float = 0.5) -> float:
        return self.trust_map.get(a, {}).get(b, default)

    def best_local_trust(self, agent_id: str, nearby_ids: list[str]) -> float:
        if not nearby_ids:
            return 0.5
        tmap = self.trust_map.get(agent_id, {})
        vals = [tmap.get(nid, 0.5) for nid in nearby_ids if nid != agent_id]
        return max(vals) if vals else 0.5

    def record_interaction(
        self,
        a_id: str,
        b_id: str,
        outcome_kind: str,  # cooperate | trade | communicate | mentor | compete | violate
        tick: int,
        base_trust_a: float = 0.5,
        base_trust_b: float = 0.5,
    ) -> RelationshipEdge | None:
        """Update dynamic trust and form/strengthen/weaken relationship edges only on repeated interaction."""
        if a_id == b_id:
            return None
        pair = self._pair(a_id, b_id)
        cur_trust_ab = self.get_trust(a_id, b_id, default=0.5 * (base_trust_a + base_trust_b))
        cur_trust_ba = self.get_trust(b_id, a_id, default=cur_trust_ab)

        if outcome_kind in ("cooperate", "mentor"):
            delta_pos = 0.14 if outcome_kind == "cooperate" else 0.16
            new_ab = min(1.0, cur_trust_ab + delta_pos * (1.0 - cur_trust_ab))
            new_ba = min(1.0, cur_trust_ba + delta_pos * (1.0 - cur_trust_ba))
            rel_type = "mentorship" if outcome_kind == "mentor" else "cooperation"
            weight_delta = 0.12
        elif outcome_kind == "trade":
            new_ab = min(1.0, cur_trust_ab + 0.09 * (1.0 - cur_trust_ab))
            new_ba = min(1.0, cur_trust_ba + 0.09 * (1.0 - cur_trust_ba))
            rel_type = "cooperation"
            weight_delta = 0.08
        elif outcome_kind == "communicate":
            new_ab = min(1.0, cur_trust_ab + 0.05 * (1.0 - cur_trust_ab))
            new_ba = min(1.0, cur_trust_ba + 0.05 * (1.0 - cur_trust_ba))
            rel_type = "friendship"
            weight_delta = 0.06
        else:  # compete | violate (trust decays faster than it grows)
            penalty = 0.22 if outcome_kind == "compete" else 0.32
            new_ab = max(0.0, cur_trust_ab - penalty * cur_trust_ab)
            new_ba = max(0.0, cur_trust_ba - (penalty * 1.25) * cur_trust_ba)
            rel_type = "rivalry"
            weight_delta = 0.10

        self.trust_map.setdefault(a_id, {})[b_id] = new_ab
        self.trust_map.setdefault(b_id, {})[a_id] = new_ba

        edge = self.edges.get(pair)
        mean_trust = 0.5 * (new_ab + new_ba)
        if edge is None:
            # First casual interaction initializes a tentative tie; permanent relationships require >=2 interactions or strong tie
            edge = RelationshipEdge(
                source_id=pair[0],
                target_id=pair[1],
                rel_type=rel_type,
                weight=min(1.0, 0.12 + weight_delta),
                trust=mean_trust,
                interaction_count=1,
                last_tick=tick,
            )
            self.edges[pair] = edge
        else:
            edge.interaction_count += 1
            edge.last_tick = tick
            edge.trust = mean_trust
            if rel_type == "rivalry":
                if edge.rel_type in ("friendship", "cooperation") and edge.trust < 0.32:
                    edge.rel_type = "rivalry"
                edge.weight = min(1.0, edge.weight + weight_delta)
            else:
                if edge.interaction_count >= 4 and edge.trust >= 0.72 and edge.rel_type == "cooperation":
                    edge.rel_type = "friendship"
                elif edge.rel_type == "rivalry" and edge.trust >= 0.55:
                    edge.rel_type = "cooperation"
                edge.weight = min(1.0, edge.weight + weight_delta)
        return edge

    def decay_stale_edges(self, current_tick: int, max_idle: int = 80) -> None:
        """Prune unreinforced transient relationships."""
        to_delete = []
        for pair, edge in self.edges.items():
            idle = current_tick - edge.last_tick
            if idle > max_idle:
                edge.weight -= 0.03
                if edge.weight <= 0.10 and edge.interaction_count < 3:
                    to_delete.append(pair)
        for pair in to_delete:
            del self.edges[pair]

    def active_edges(self, min_interactions: int = 2) -> list[RelationshipEdge]:
        return [e for e in self.edges.values() if e.interaction_count >= min_interactions]

    def to_networkx(self, agent_ids: list[str], min_interactions: int = 2) -> nx.Graph:
        g = nx.Graph()
        g.add_nodes_from(agent_ids)
        for e in self.edges.values():
            if e.interaction_count >= min_interactions and e.rel_type != "rivalry" and e.weight >= 0.18:
                g.add_edge(e.source_id, e.target_id, weight=e.weight, trust=e.trust, rel_type=e.rel_type)
        return g

    def detect_communities(
        self,
        agents_by_id: dict[str, Any],
        world_locations: dict[str, Any],
        tick: int,
        min_size: int = 3,
    ) -> dict[str, Community]:
        """Detect emergent communities via NetworkX greedy modularity on active positive relationships."""
        alive_ids = [aid for aid, ag in agents_by_id.items() if ag.alive]
        g = self.to_networkx(alive_ids, min_interactions=2)
        if g.number_of_edges() == 0:
            self.communities = {}
            for ag in agents_by_id.values():
                ag.community_id = None
            return self.communities

        raw_comms = list(nx.community.greedy_modularity_communities(g, weight="weight"))
        new_comms: dict[str, Community] = {}
        for ag in agents_by_id.values():
            ag.community_id = None

        c_idx = 1
        for group in raw_comms:
            members = sorted(group)
            if len(members) < min_size:
                continue
            sub = g.subgraph(members)
            possible = len(members) * (len(members) - 1) / 2
            cohesion = sub.number_of_edges() / possible if possible > 0 else 0.0
            xs = [world_locations[agents_by_id[m].location_id].x for m in members]
            ys = [world_locations[agents_by_id[m].location_id].y for m in members]
            cid = f"comm_{c_idx:03d}"
            c_idx += 1
            comm = Community(
                community_id=cid,
                name=f"Cluster {c_idx - 1}",
                founded_tick=self.communities[cid].founded_tick if cid in self.communities else tick,
                member_ids=members,
                cohesion=cohesion,
                centroid_x=sum(xs) / len(xs),
                centroid_y=sum(ys) / len(ys),
            )
            new_comms[cid] = comm
            for m in members:
                agents_by_id[m].community_id = cid

        self.communities = new_comms
        return self.communities

    def mean_trust(self) -> float:
        edges = self.active_edges(min_interactions=1)
        if not edges:
            return 0.5
        return sum(e.trust for e in edges) / len(edges)

    def network_density(self, population: int) -> float:
        if population < 2:
            return 0.0
        active = len([e for e in self.edges.values() if e.interaction_count >= 2])
        possible = population * (population - 1) / 2
        return min(1.0, active / possible)

    def to_dict(self) -> dict[str, Any]:
        return {
            "edges": [e.to_dict() for e in self.edges.values()],
            "trust_map": {k: dict(v) for k, v in self.trust_map.items()},
            "communities": {k: v.to_dict() for k, v in self.communities.items()},
        }

    def to_snapshot_dict(self) -> dict[str, Any]:
        return {
            "edges": [
                {
                    "source_id": e.source_id,
                    "target_id": e.target_id,
                    "rel_type": e.rel_type,
                    "weight": e.weight,
                    "trust": e.trust,
                    "interaction_count": e.interaction_count,
                    "last_tick": e.last_tick,
                }
                for e in self.edges.values()
            ],
            "trust_map": {k: dict(v) for k, v in self.trust_map.items()},
            "communities": {
                k: {
                    "community_id": v.community_id,
                    "name": v.name,
                    "founded_tick": v.founded_tick,
                    "member_ids": list(v.member_ids),
                    "cohesion": v.cohesion,
                    "centroid_x": v.centroid_x,
                    "centroid_y": v.centroid_y,
                }
                for k, v in self.communities.items()
            },
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> SocialNetwork:
        net = cls()
        for ed in d.get("edges", []):
            edge = RelationshipEdge.from_dict(ed)
            net.edges[cls._pair(edge.source_id, edge.target_id)] = edge
        net.trust_map = {
            k: {ok: float(ov) for ok, ov in v.items()}
            for k, v in d.get("trust_map", {}).items()
        }
        for cid, cd in d.get("communities", {}).items():
            net.communities[cid] = Community(
                community_id=cd["community_id"],
                name=cd["name"],
                founded_tick=int(cd["founded_tick"]),
                member_ids=list(cd["member_ids"]),
                cohesion=float(cd["cohesion"]),
                centroid_x=float(cd["centroid_x"]),
                centroid_y=float(cd["centroid_y"]),
            )
        return net
