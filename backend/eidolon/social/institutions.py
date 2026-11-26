"""Rule-governed institutions with membership, treasuries, redistribution, compliance, and dissolution."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from eidolon.world.resources import RESOURCE_TYPES, empty_inventory, transfer_resource

if TYPE_CHECKING:
    from eidolon.agent.cognition import Agent
    from eidolon.social.relationships import SocialNetwork


@dataclass
class InstitutionMember:
    agent_id: str
    role: str  # founder | steward | member
    joined_tick: int
    contribution: float = 0.0
    violations: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "role": self.role,
            "joined_tick": self.joined_tick,
            "contribution": round(self.contribution, 4),
            "violations": self.violations,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> InstitutionMember:
        return cls(
            agent_id=d["agent_id"],
            role=d["role"],
            joined_tick=int(d["joined_tick"]),
            contribution=float(d.get("contribution", 0.0)),
            violations=int(d.get("violations", 0)),
        )


@dataclass
class Institution:
    institution_id: str
    name: str
    inst_type: str  # resource_pool | market_guild | council | academy
    founder_id: str
    founded_tick: int
    location_id: str
    stability: float = 0.75
    treasury: dict[str, float] = field(default_factory=empty_inventory)
    rules: dict[str, float] = field(default_factory=dict)
    members: dict[str, InstitutionMember] = field(default_factory=dict)
    compliance_rate: float = 1.0
    active: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "institution_id": self.institution_id,
            "name": self.name,
            "inst_type": self.inst_type,
            "founder_id": self.founder_id,
            "founded_tick": self.founded_tick,
            "location_id": self.location_id,
            "stability": round(self.stability, 4),
            "treasury": {k: round(v, 4) for k, v in self.treasury.items()},
            "rules": dict(self.rules),
            "members": {k: v.to_dict() for k, v in self.members.items()},
            "member_count": len(self.members),
            "compliance_rate": round(self.compliance_rate, 4),
            "active": self.active,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Institution:
        return cls(
            institution_id=d["institution_id"],
            name=d["name"],
            inst_type=d["inst_type"],
            founder_id=d["founder_id"],
            founded_tick=int(d["founded_tick"]),
            location_id=d["location_id"],
            stability=float(d.get("stability", 0.75)),
            treasury={k: float(v) for k, v in d.get("treasury", {}).items()},
            rules={k: float(v) for k, v in d.get("rules", {}).items()},
            members={k: InstitutionMember.from_dict(v) for k, v in d.get("members", {}).items()},
            compliance_rate=float(d.get("compliance_rate", 1.0)),
            active=bool(d.get("active", True)),
        )


class InstitutionRegistry:
    """Manages emergent creation, rule enforcement, treasury redistribution, and dissolution of institutions."""

    def __init__(self) -> None:
        self.institutions: dict[str, Institution] = {}
        self.agent_institution: dict[str, str] = {}
        self._counter: int = 0

    def get_for_agent(self, agent_id: str) -> Institution | None:
        iid = self.agent_institution.get(agent_id)
        if not iid:
            return None
        inst = self.institutions.get(iid)
        if inst and inst.active:
            return inst
        return None

    def try_form_institutions(
        self,
        agents_by_location: dict[str, list[Agent]],
        network: SocialNetwork,
        tick: int,
        enabled: bool = True,
        min_trust_threshold: float = 0.58,
    ) -> list[Institution]:
        """Organically create institutions only when co-located agents satisfy trust & interaction thresholds."""
        if not enabled:
            return []
        created: list[Institution] = []
        for loc_id, local_agents in agents_by_location.items():
            unaffiliated = [ag for ag in local_agents if ag.alive and ag.agent_id not in self.agent_institution]
            if len(unaffiliated) < 4:
                continue

            # Check whether a cohesive core of >=4 agents has strong mutual trust & interaction history
            candidates: list[Agent] = []
            for ag in unaffiliated:
                trusted_peers = 0
                for other in unaffiliated:
                    if other.agent_id == ag.agent_id:
                        continue
                    if network.get_trust(ag.agent_id, other.agent_id, 0.5) >= min_trust_threshold:
                        trusted_peers += 1
                if trusted_peers >= 2:
                    candidates.append(ag)

            if len(candidates) < 4:
                continue

            cohort = candidates[:8]
            mean_open = sum(a.traits.openness for a in cohort) / len(cohort)
            mean_agree = sum(a.traits.agreeableness for a in cohort) / len(cohort)
            mean_consc = sum(a.traits.conscientiousness for a in cohort) / len(cohort)

            if mean_open > 0.58:
                inst_type = "academy"
                label = "Scholarly Academy"
                rules = {"contribution_rate": 0.08, "redistribution_ratio": 0.45, "knowledge_bonus": 0.25}
            elif mean_consc > 0.58 and mean_agree < 0.58:
                inst_type = "market_guild"
                label = "Trade Guild"
                rules = {"contribution_rate": 0.10, "redistribution_ratio": 0.35, "trade_bonus": 0.20}
            elif mean_agree >= 0.56:
                inst_type = "resource_pool"
                label = "Mutual Aid Pool"
                rules = {"contribution_rate": 0.14, "redistribution_ratio": 0.65, "coop_bonus": 0.20}
            else:
                inst_type = "council"
                label = "Civic Council"
                rules = {"contribution_rate": 0.10, "redistribution_ratio": 0.50, "safety_bonus": 0.20}

            self._counter += 1
            iid = f"inst_{self._counter:03d}"
            founder = max(cohort, key=lambda a: a.reputation)
            members = {
                ag.agent_id: InstitutionMember(
                    agent_id=ag.agent_id,
                    role="founder" if ag.agent_id == founder.agent_id else "member",
                    joined_tick=tick,
                )
                for ag in cohort
            }
            inst = Institution(
                institution_id=iid,
                name=f"{label} #{self._counter}",
                inst_type=inst_type,
                founder_id=founder.agent_id,
                founded_tick=tick,
                location_id=loc_id,
                stability=0.78,
                rules=rules,
                members=members,
            )
            self.institutions[iid] = inst
            for aid in members:
                self.agent_institution[aid] = iid
            created.append(inst)
        return created

    def step_institutions(
        self,
        agents_by_id: dict[str, Agent],
        tick: int,
    ) -> list[dict[str, Any]]:
        """Collect rule-based surplus dues, redistribute to needy members, and check dissolution."""
        events: list[dict[str, Any]] = []
        for inst in list(self.institutions.values()):
            if not inst.active:
                continue

            # Remove dead or departed members who left due to low compliance
            for aid in list(inst.members.keys()):
                ag = agents_by_id.get(aid)
                if ag is None or not ag.alive:
                    inst.members.pop(aid, None)
                    self.agent_institution.pop(aid, None)

            if len(inst.members) < 2 or inst.stability < 0.20:
                inst.active = False
                for aid in list(inst.members.keys()):
                    self.agent_institution.pop(aid, None)
                events.append(
                    {
                        "event_type": "institution_dissolved",
                        "institution_id": inst.institution_id,
                        "name": inst.name,
                        "tick": tick,
                    }
                )
                continue

            contrib_rate = inst.rules.get("contribution_rate", 0.10)
            redist_ratio = inst.rules.get("redistribution_ratio", 0.50)

            # 1. Dues collection from surplus
            total_violations = 0
            for aid, mem in inst.members.items():
                ag = agents_by_id[aid]
                contributed_any = False
                for r in ("food", "water", "raw_materials"):
                    surplus = ag.resources.get(r, 0.0) - 2.0
                    if surplus > 0.5:
                        due = min(0.4, surplus * contrib_rate)
                        moved = transfer_resource(ag.resources, inst.treasury, r, due)
                        mem.contribution += moved
                        contributed_any = True
                if contributed_any:
                    ag.needs.adjust("belonging", 0.03)
                total_violations += mem.violations

            # 2. Redistribution to members with low nutrition or low reserves
            for aid in inst.members:
                ag = agents_by_id[aid]
                if ag.needs.nutrition < 0.50 or ag.resources.get("food", 0.0) < 1.0:
                    grant = min(inst.treasury.get("food", 0.0) * redist_ratio, 0.8)
                    if grant > 0.1:
                        transfer_resource(inst.treasury, ag.resources, "food", grant)
                        ag.needs.adjust("safety", 0.04)
                if ag.resources.get("water", 0.0) < 1.0:
                    w_grant = min(inst.treasury.get("water", 0.0) * redist_ratio, 0.8)
                    if w_grant > 0.1:
                        transfer_resource(inst.treasury, ag.resources, "water", w_grant)

                # Institutional structural bonus
                if inst.inst_type == "council":
                    ag.needs.adjust("safety", 0.015)
                elif inst.inst_type == "academy":
                    ag.needs.adjust("knowledge_acquisition", 0.015)

            # 3. Compliance & stability update
            n_mem = len(inst.members)
            inst.compliance_rate = max(0.0, min(1.0, 1.0 - (total_violations / max(1, n_mem * 3))))
            treasury_health = min(1.0, sum(inst.treasury.values()) / max(1.0, n_mem * 2.5))
            target_stab = 0.55 * inst.compliance_rate + 0.30 * treasury_health + 0.15 * min(1.0, n_mem / 8.0)
            inst.stability = max(0.0, min(1.0, 0.85 * inst.stability + 0.15 * target_stab))

        return events

    def record_violation(self, agent_id: str) -> None:
        inst = self.get_for_agent(agent_id)
        if inst and agent_id in inst.members:
            inst.members[agent_id].violations += 1
            inst.stability = max(0.0, inst.stability - 0.04)

    def active_list(self) -> list[dict[str, Any]]:
        return [i.to_dict() for i in self.institutions.values() if i.active]

    def mean_stability(self) -> float:
        act = [i.stability for i in self.institutions.values() if i.active]
        return sum(act) / len(act) if act else 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "counter": self._counter,
            "institutions": {k: v.to_dict() for k, v in self.institutions.items()},
            "agent_institution": dict(self.agent_institution),
        }

    def to_snapshot_dict(self) -> dict[str, Any]:
        return {
            "counter": self._counter,
            "institutions": {
                k: {
                    "institution_id": inst.institution_id,
                    "name": inst.name,
                    "inst_type": inst.inst_type,
                    "founder_id": inst.founder_id,
                    "founded_tick": inst.founded_tick,
                    "location_id": inst.location_id,
                    "stability": inst.stability,
                    "treasury": dict(inst.treasury),
                    "rules": dict(inst.rules),
                    "members": {
                        mk: {
                            "agent_id": m.agent_id,
                            "role": m.role,
                            "joined_tick": m.joined_tick,
                            "contribution": m.contribution,
                            "violations": m.violations,
                        }
                        for mk, m in inst.members.items()
                    },
                    "compliance_rate": inst.compliance_rate,
                    "active": inst.active,
                }
                for k, inst in self.institutions.items()
            },
            "agent_institution": dict(self.agent_institution),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> InstitutionRegistry:
        reg = cls()
        reg._counter = int(d.get("counter", 0))
        reg.institutions = {
            k: Institution.from_dict(v) for k, v in d.get("institutions", {}).items()
        }
        reg.agent_institution = dict(d.get("agent_institution", {}))
        return reg
