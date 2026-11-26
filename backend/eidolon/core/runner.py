"""Simulation runtime manager handling active engines, background execution, and WebSocket broadcasts."""

from __future__ import annotations

import asyncio
import uuid
from typing import Any

from eidolon.core.engine import ExperimentConfig, SimulationEngine
from eidolon.persistence.database import Database
from eidolon.persistence.repository import ExperimentRepository
from eidolon.scenarios.presets import get_scenario_config


class SimulationManager:
    """Coordinates active simulations, background async execution, and DB persistence."""

    def __init__(self, db: Database | None = None) -> None:
        self.db = db or Database()
        self.repo = ExperimentRepository(self.db)
        self.engines: dict[str, SimulationEngine] = {}
        self.active_experiment_id: str | None = None
        self.running_tasks: dict[str, asyncio.Task[Any]] = {}
        self.run_states: dict[str, str] = {}  # created | running | paused | stopped | completed
        self.tick_interval_sec: float = 0.12
        self.subscribers: list[asyncio.Queue[dict[str, Any]]] = []
        self.error_logs: list[dict[str, Any]] = []

    def ensure_default_experiment(self) -> SimulationEngine:
        if self.active_experiment_id and self.active_experiment_id in self.engines:
            return self.engines[self.active_experiment_id]
        existing = self.repo.list_experiments()
        if existing:
            eid = existing[0]["id"]
            restored = self.repo.latest_snapshot_for_experiment(eid)
            if restored:
                self.engines[eid] = restored
                self.active_experiment_id = eid
                self.run_states[eid] = existing[0]["status"]
                return restored
        cfg = get_scenario_config("cooperation_experiment")
        return self.create_experiment(cfg)

    def create_experiment(self, config: ExperimentConfig, experiment_id: str | None = None) -> SimulationEngine:
        eid = experiment_id or f"exp_{uuid.uuid4().hex[:8]}"
        engine = SimulationEngine(experiment_id=eid, config=config)
        self.engines[eid] = engine
        self.active_experiment_id = eid
        self.run_states[eid] = "created"
        self.repo.create_experiment_record(engine, status="created")
        self.repo.save_snapshot(engine, label="initial_state")
        return engine

    def duplicate_experiment(self, source_id: str, new_name: str | None = None, seed: int | None = None) -> SimulationEngine:
        src = self.get_engine(source_id)
        cfg_dict = src.config.to_dict()
        cfg_dict["name"] = new_name or f"{src.config.name} (Copy)"
        if seed is not None:
            cfg_dict["seed"] = int(seed)
        return self.create_experiment(ExperimentConfig.from_dict(cfg_dict))

    def get_engine(self, experiment_id: str | None = None) -> SimulationEngine:
        eid = experiment_id or self.active_experiment_id
        if not eid:
            return self.ensure_default_experiment()
        if eid in self.engines:
            return self.engines[eid]
        snap = self.repo.latest_snapshot_for_experiment(eid)
        if snap:
            self.engines[eid] = snap
            self.run_states[eid] = "paused"
            return snap
        rec = self.repo.get_experiment(eid)
        if rec:
            cfg = ExperimentConfig.from_dict(rec["config"])
            eng = SimulationEngine(experiment_id=eid, config=cfg)
            self.engines[eid] = eng
            self.run_states[eid] = rec["status"]
            return eng
        raise KeyError(f"Experiment not found: {eid}")

    def select_experiment(self, experiment_id: str) -> SimulationEngine:
        eng = self.get_engine(experiment_id)
        self.active_experiment_id = experiment_id
        return eng

    def step_once(self, experiment_id: str | None = None, steps: int = 1) -> list[dict[str, Any]]:
        eng = self.get_engine(experiment_id)
        rows = []
        for _ in range(max(1, steps)):
            rows.append(eng.step())
        self.repo.flush_tick_batches(eng, rows)
        if eng.clock.tick % 20 == 0:
            self.repo.sync_world_and_agents(eng)
        return rows

    async def start_running(self, experiment_id: str | None = None, tick_interval_ms: int = 120) -> str:
        eng = self.get_engine(experiment_id)
        eid = eng.experiment_id
        self.active_experiment_id = eid
        self.tick_interval_sec = max(0.01, tick_interval_ms / 1000.0)

        existing_task = self.running_tasks.get(eid)
        if existing_task and not existing_task.done():
            self.run_states[eid] = "running"
            return eid

        self.run_states[eid] = "running"
        self.repo.update_experiment_status(eid, "running", eng.clock.tick)
        self.running_tasks[eid] = asyncio.create_task(self._run_loop(eid))
        return eid

    async def pause(self, experiment_id: str | None = None) -> None:
        eid = experiment_id or self.active_experiment_id
        if not eid:
            return
        self.run_states[eid] = "paused"
        task = self.running_tasks.pop(eid, None)
        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        eng = self.engines.get(eid)
        if eng:
            self.repo.sync_world_and_agents(eng)
            self.repo.update_experiment_status(eid, "paused", eng.clock.tick)

    async def stop(self, experiment_id: str | None = None) -> None:
        eid = experiment_id or self.active_experiment_id
        if not eid:
            return
        await self.pause(eid)
        self.run_states[eid] = "stopped"
        eng = self.engines.get(eid)
        if eng:
            self.repo.save_snapshot(eng, label="stopped")
            self.repo.update_experiment_status(eid, "stopped", eng.clock.tick)

    async def _run_loop(self, eid: str) -> None:
        eng = self.engines[eid]
        batch_metrics: list[dict[str, Any]] = []
        try:
            while self.run_states.get(eid) == "running":
                if eng.clock.tick >= eng.config.duration_ticks:
                    self.run_states[eid] = "completed"
                    self.repo.flush_tick_batches(eng, batch_metrics)
                    batch_metrics.clear()
                    self.repo.save_snapshot(eng, label="completed")
                    self.repo.update_experiment_status(eid, "completed", eng.clock.tick)
                    await self._broadcast(eng, completed=True)
                    break

                metric = eng.step()
                batch_metrics.append(metric)
                if len(batch_metrics) >= 5:
                    self.repo.flush_tick_batches(eng, batch_metrics)
                    batch_metrics.clear()
                if eng.clock.tick % 25 == 0:
                    self.repo.sync_world_and_agents(eng)
                if eng.clock.tick % 50 == 0:
                    self.repo.save_snapshot(eng, label=f"auto_tick_{eng.clock.tick}")

                await self._broadcast(eng, completed=False)
                await asyncio.sleep(self.tick_interval_sec)
        except asyncio.CancelledError:
            if batch_metrics:
                self.repo.flush_tick_batches(eng, batch_metrics)
            raise
        except Exception as exc:
            self.error_logs.append({"tick": eng.clock.tick, "experiment_id": eid, "error": str(exc)})
            self.run_states[eid] = "error"
            if batch_metrics:
                self.repo.flush_tick_batches(eng, batch_metrics)

    async def _broadcast(self, eng: SimulationEngine, completed: bool = False) -> None:
        if not self.subscribers:
            return
        payload = {
            "type": "tick_update",
            "completed": completed,
            "status": self.run_states.get(eng.experiment_id, "paused"),
            "summary": eng.state_summary(),
            "agents": [
                {
                    "agent_id": ag.agent_id,
                    "name": ag.name,
                    "location_id": ag.location_id,
                    "occupation": ag.occupation,
                    "community_id": ag.community_id,
                    "last_action": ag.last_action,
                    "mean_need_satisfaction": round(ag.needs.mean_satisfaction(), 3),
                    "reputation": round(ag.reputation, 3),
                }
                for ag in eng.agents.values()
                if ag.alive
            ],
            "locations": [loc.to_dict() for loc in eng.world.locations.values()],
        }
        for q in list(self.subscribers):
            if q.full():
                try:
                    q.get_nowait()
                except asyncio.QueueEmpty:
                    pass
            await q.put(payload)

    def subscribe(self) -> asyncio.Queue[dict[str, Any]]:
        q: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=4)
        self.subscribers.append(q)
        return q

    def unsubscribe(self, q: asyncio.Queue[dict[str, Any]]) -> None:
        if q in self.subscribers:
            self.subscribers.remove(q)
