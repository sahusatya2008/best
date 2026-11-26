"""Normalized SQLite repository for batched persistence, snapshots, and experiment import/export."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from eidolon.core.engine import ExperimentConfig, SimulationEngine
from eidolon.persistence.database import Database


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ExperimentRepository:
    """Handles structured persistence, snapshots, and relational queries in SQLite."""

    def __init__(self, db: Database) -> None:
        self.db = db

    def create_experiment_record(self, engine: SimulationEngine, status: str = "created") -> None:
        now = _now_iso()
        with self.db.transaction() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO experiments
                (id, name, description, scenario_id, seed, status, current_tick, config_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    engine.experiment_id,
                    engine.config.name,
                    engine.config.description,
                    engine.config.scenario_id,
                    engine.config.seed,
                    status,
                    engine.clock.tick,
                    json.dumps(engine.config.to_dict()),
                    now,
                    now,
                ),
            )
        self.sync_world_and_agents(engine)

    def update_experiment_status(self, experiment_id: str, status: str, tick: int) -> None:
        with self.db.transaction() as conn:
            conn.execute(
                "UPDATE experiments SET status = ?, current_tick = ?, updated_at = ? WHERE id = ?",
                (status, tick, _now_iso(), experiment_id),
            )

    def sync_world_and_agents(self, engine: SimulationEngine) -> None:
        """Persist current normalized relational tables for locations, agents, social ties, institutions, and metrics."""
        eid = engine.experiment_id
        tick = engine.clock.tick
        with self.db.transaction() as conn:
            # Locations & stocks
            loc_rows = []
            stock_rows = []
            for loc in engine.world.locations.values():
                loc_rows.append(
                    (eid, loc.location_id, loc.name, loc.region, loc.kind, loc.x, loc.y, loc.fertility, loc.hazard_level, loc.capacity)
                )
                for r_type, st in loc.resources.items():
                    stock_rows.append((eid, loc.location_id, r_type, st.quantity, st.max_capacity, st.regen_rate))
            conn.executemany(
                """
                INSERT OR REPLACE INTO locations
                (experiment_id, location_id, name, region, kind, x, y, fertility, hazard_level, capacity)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                loc_rows,
            )
            conn.executemany(
                """
                INSERT OR REPLACE INTO location_resources
                (experiment_id, location_id, resource_type, quantity, max_capacity, regen_rate)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                stock_rows,
            )

            # Agents, traits, states, resources, goals, beliefs, cultural traits
            ag_rows, trait_rows, state_rows, res_rows, goal_rows, belief_rows, cult_rows = [], [], [], [], [], [], []
            for ag in engine.agents.values():
                ag_rows.append(
                    (
                        eid, ag.agent_id, ag.name, ag.birth_tick, ag.age, ag.generation,
                        ag.occupation, ag.social_status, ag.location_id, ag.home_location_id,
                        ag.community_id, 1 if ag.alive else 0,
                    )
                )
                t = ag.traits
                trait_rows.append((eid, ag.agent_id, t.openness, t.conscientiousness, t.extraversion, t.agreeableness, t.emotional_stability))
                n = ag.needs
                state_rows.append(
                    (
                        eid, ag.agent_id, n.nutrition, n.energy, n.safety, n.social_connection,
                        n.belonging, n.achievement, n.knowledge_acquisition, n.resource_security,
                        ag.last_action, ag.last_reward, ag.cumulative_reward, ag.reputation,
                    )
                )
                for r_type, qty in ag.resources.items():
                    res_rows.append((eid, ag.agent_id, r_type, qty))
                for g in ag.goals:
                    goal_rows.append((eid, ag.agent_id, g.goal_id, g.goal_type, g.target_value, g.priority, g.progress, 1 if g.active else 0))
                for bk, bv in ag.beliefs.items():
                    belief_rows.append((eid, ag.agent_id, bk, bv.value, bv.confidence, bv.updated_tick))
                for tn, tv in ag.cultural_traits.items():
                    cult_rows.append((eid, ag.agent_id, tn, tv, tick, None))

            conn.executemany(
                """
                INSERT OR REPLACE INTO agents
                (experiment_id, agent_id, name, birth_tick, age, generation, occupation, social_status, location_id, home_location_id, community_id, alive)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                ag_rows,
            )
            conn.executemany(
                """
                INSERT OR REPLACE INTO agent_traits
                (experiment_id, agent_id, openness, conscientiousness, extraversion, agreeableness, emotional_stability)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                trait_rows,
            )
            conn.executemany(
                """
                INSERT OR REPLACE INTO agent_states
                (experiment_id, agent_id, nutrition, energy, safety, social_connection, belonging, achievement, knowledge_acquisition, resource_security, last_action, last_reward, cumulative_reward, reputation)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                state_rows,
            )
            conn.executemany(
                "INSERT OR REPLACE INTO agent_resources (experiment_id, agent_id, resource_type, quantity) VALUES (?, ?, ?, ?)",
                res_rows,
            )
            conn.executemany(
                """
                INSERT OR REPLACE INTO agent_goals
                (experiment_id, agent_id, goal_id, goal_type, target_value, priority, progress, active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                goal_rows,
            )
            conn.executemany(
                """
                INSERT OR REPLACE INTO agent_beliefs
                (experiment_id, agent_id, belief_key, belief_value, confidence, updated_tick)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                belief_rows,
            )
            conn.executemany(
                """
                INSERT OR REPLACE INTO cultural_traits
                (experiment_id, agent_id, trait_name, trait_value, adoption_tick, source_agent_id)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                cult_rows,
            )

            # Relationships
            rel_rows = [
                (eid, e.source_id, e.target_id, e.rel_type, e.weight, e.trust, e.interaction_count, e.last_tick)
                for e in engine.network.edges.values()
            ]
            if rel_rows:
                conn.executemany(
                    """
                    INSERT OR REPLACE INTO relationships
                    (experiment_id, source_agent_id, target_agent_id, rel_type, weight, trust, interaction_count, last_tick)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    rel_rows,
                )

            # Communities
            conn.execute("DELETE FROM communities WHERE experiment_id = ?", (eid,))
            comm_rows = [
                (eid, c.community_id, c.name, c.founded_tick, c.cohesion, c.centroid_x, c.centroid_y, len(c.member_ids))
                for c in engine.network.communities.values()
            ]
            if comm_rows:
                conn.executemany(
                    """
                    INSERT INTO communities
                    (experiment_id, community_id, name, founded_tick, cohesion, centroid_x, centroid_y, member_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    comm_rows,
                )

            # Institutions
            inst_rows = []
            inst_mem_rows = []
            for inst in engine.institutions.institutions.values():
                inst_rows.append(
                    (
                        eid, inst.institution_id, inst.name, inst.inst_type, inst.founder_id,
                        inst.founded_tick, inst.stability, json.dumps(inst.treasury),
                        json.dumps(inst.rules), inst.compliance_rate, 1 if inst.active else 0,
                    )
                )
                for m in inst.members.values():
                    inst_mem_rows.append((eid, inst.institution_id, m.agent_id, m.role, m.joined_tick, m.contribution, m.violations))
            if inst_rows:
                conn.executemany(
                    """
                    INSERT OR REPLACE INTO institutions
                    (experiment_id, institution_id, name, inst_type, founder_id, founded_tick, stability, treasury_json, rules_json, compliance_rate, active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    inst_rows,
                )
            if inst_mem_rows:
                conn.executemany(
                    """
                    INSERT OR REPLACE INTO institution_members
                    (experiment_id, institution_id, agent_id, role, joined_tick, contribution, violations)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    inst_mem_rows,
                )

    def flush_tick_batches(self, engine: SimulationEngine, metric_rows: list[dict[str, Any]]) -> None:
        """Batch-persist pending events, metrics, learning records, and recent agent memories."""
        eid = engine.experiment_id
        pending_events = engine.events.drain_pending()
        with self.db.transaction() as conn:
            conn.execute(
                "UPDATE experiments SET current_tick = ?, updated_at = ? WHERE id = ?",
                (engine.clock.tick, _now_iso(), eid),
            )
            if metric_rows:
                conn.executemany(
                    """
                    INSERT OR REPLACE INTO metrics
                    (experiment_id, tick, population, total_resources, cooperation_index, gini_coefficient,
                     mean_trust, network_density, community_count, institution_count, cultural_diversity,
                     mean_q_value, mean_utility, trade_volume, collective_success_rate, avg_need_satisfaction)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            eid, m["tick"], m["population"], m["total_resources"], m["cooperation_index"],
                            m["gini_coefficient"], m["mean_trust"], m["network_density"], m["community_count"],
                            m["institution_count"], m["cultural_diversity"], m["mean_q_value"], m["mean_utility"],
                            m["trade_volume"], m["collective_success_rate"], m["avg_need_satisfaction"],
                        )
                        for m in metric_rows
                    ],
                )
            if pending_events:
                conn.executemany(
                    """
                    INSERT INTO events
                    (experiment_id, tick, event_type, actor_id, target_id, location_id, payload_json, explanation_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            eid, ev.tick, ev.event_type, ev.actor_id, ev.target_id, ev.location_id,
                            json.dumps(ev.payload), json.dumps(ev.explanation) if ev.explanation else None,
                        )
                        for ev in pending_events
                    ],
                )

            # Persist latest learning record per agent for latest tick
            learn_rows = []
            mem_rows = []
            curr_tick = engine.clock.tick
            for ag in engine.agents.values():
                if ag.q_learner.recent_records and ag.q_learner.recent_records[-1].tick == curr_tick:
                    lr = ag.q_learner.recent_records[-1]
                    learn_rows.append((eid, ag.agent_id, lr.tick, lr.state_key, lr.action, lr.q_value, lr.reward, lr.next_state_key, lr.td_error, lr.source))
                if ag.memory.episodic and ag.memory.episodic[-1].tick == curr_tick:
                    em = ag.memory.episodic[-1]
                    mem_rows.append(
                        (
                            eid, ag.agent_id, em.layer, em.tick, em.event_type,
                            json.dumps(em.participants), json.dumps(em.context), em.outcome,
                            em.emotional_significance, em.relevance_weight, em.recall_count, 1 if em.consolidated else 0,
                        )
                    )
            if learn_rows:
                conn.executemany(
                    """
                    INSERT INTO learning_records
                    (experiment_id, agent_id, tick, state_key, action, q_value, reward, next_state_key, td_error, source)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    learn_rows,
                )
            if mem_rows:
                conn.executemany(
                    """
                    INSERT INTO agent_memories
                    (experiment_id, agent_id, memory_layer, tick, event_type, participants_json, context_json, outcome, emotional_significance, relevance_weight, recall_count, consolidated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    mem_rows,
                )

    def save_snapshot(self, engine: SimulationEngine, label: str = "checkpoint") -> dict[str, Any]:
        blob, checksum = engine.to_snapshot_bytes()
        snap_id = f"snap_{uuid.uuid4().hex[:10]}"
        created = _now_iso()
        with self.db.transaction() as conn:
            conn.execute(
                """
                INSERT INTO simulation_snapshots
                (id, experiment_id, tick, label, state_blob, checksum, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (snap_id, engine.experiment_id, engine.clock.tick, label, blob, checksum, created),
            )
        self.sync_world_and_agents(engine)
        return {
            "snapshot_id": snap_id,
            "experiment_id": engine.experiment_id,
            "tick": engine.clock.tick,
            "label": label,
            "checksum": checksum,
            "size_bytes": len(blob),
            "created_at": created,
        }

    def load_snapshot(self, snapshot_id: str) -> SimulationEngine:
        with self.db.connect() as conn:
            row = conn.execute(
                "SELECT state_blob, checksum FROM simulation_snapshots WHERE id = ?",
                (snapshot_id,),
            ).fetchone()
        if row is None:
            raise KeyError(f"Snapshot not found: {snapshot_id}")
        return SimulationEngine.from_snapshot_bytes(bytes(row["state_blob"]), row["checksum"])

    def latest_snapshot_for_experiment(self, experiment_id: str) -> SimulationEngine | None:
        with self.db.connect() as conn:
            row = conn.execute(
                "SELECT id FROM simulation_snapshots WHERE experiment_id = ? ORDER BY tick DESC, created_at DESC LIMIT 1",
                (experiment_id,),
            ).fetchone()
        if row is None:
            return None
        return self.load_snapshot(row["id"])

    def list_snapshots(self, experiment_id: str | None = None) -> list[dict[str, Any]]:
        with self.db.connect() as conn:
            if experiment_id:
                rows = conn.execute(
                    "SELECT id, experiment_id, tick, label, checksum, length(state_blob) as size_bytes, created_at FROM simulation_snapshots WHERE experiment_id = ? ORDER BY tick DESC",
                    (experiment_id,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT id, experiment_id, tick, label, checksum, length(state_blob) as size_bytes, created_at FROM simulation_snapshots ORDER BY created_at DESC LIMIT 50"
                ).fetchall()
        return [
            {
                "snapshot_id": r["id"],
                "experiment_id": r["experiment_id"],
                "tick": r["tick"],
                "label": r["label"],
                "checksum": r["checksum"],
                "size_bytes": r["size_bytes"],
                "created_at": r["created_at"],
            }
            for r in rows
        ]

    def list_experiments(self) -> list[dict[str, Any]]:
        with self.db.connect() as conn:
            rows = conn.execute(
                "SELECT id, name, description, scenario_id, seed, status, current_tick, config_json, created_at, updated_at FROM experiments ORDER BY updated_at DESC"
            ).fetchall()
        return [
            {
                "id": r["id"],
                "name": r["name"],
                "description": r["description"],
                "scenario_id": r["scenario_id"],
                "seed": r["seed"],
                "status": r["status"],
                "current_tick": r["current_tick"],
                "config": json.loads(r["config_json"]),
                "created_at": r["created_at"],
                "updated_at": r["updated_at"],
            }
            for r in rows
        ]

    def get_experiment(self, experiment_id: str) -> dict[str, Any] | None:
        with self.db.connect() as conn:
            r = conn.execute(
                "SELECT id, name, description, scenario_id, seed, status, current_tick, config_json, created_at, updated_at FROM experiments WHERE id = ?",
                (experiment_id,),
            ).fetchone()
        if r is None:
            return None
        return {
            "id": r["id"],
            "name": r["name"],
            "description": r["description"],
            "scenario_id": r["scenario_id"],
            "seed": r["seed"],
            "status": r["status"],
            "current_tick": r["current_tick"],
            "config": json.loads(r["config_json"]),
            "created_at": r["created_at"],
            "updated_at": r["updated_at"],
        }

    def get_metrics(self, experiment_id: str) -> list[dict[str, Any]]:
        with self.db.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM metrics WHERE experiment_id = ? ORDER BY tick ASC",
                (experiment_id,),
            ).fetchall()
        return [dict(r) for r in rows]

    def delete_experiment(self, experiment_id: str) -> None:
        with self.db.transaction() as conn:
            conn.execute("DELETE FROM experiments WHERE id = ?", (experiment_id,))
