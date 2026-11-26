"""FastAPI router exposing all simulation, cognitive, social, analytics, and persistence endpoints."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import psutil
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import FileResponse

from eidolon.analytics.comparison import compare_saved_histories, run_controlled_comparison
from eidolon.analytics.emergence import detect_emergent_patterns
from eidolon.analytics.metrics import compute_network_analytics, compute_wealth_distribution
from eidolon.analytics.reports import export_experiment_bundle
from eidolon.api.schemas import (
    CompareSavedRequest,
    CreateExperimentRequest,
    DuplicateExperimentRequest,
    ImportExperimentRequest,
    LiveConfigPatchRequest,
    RunSimulationRequest,
    SaveSnapshotRequest,
    StepSimulationRequest,
)
from eidolon.config import EXPORTS_DIR, REPORTS_DIR
from eidolon.core.engine import ExperimentConfig
from eidolon.core.runner import SimulationManager
from eidolon.scenarios.presets import get_scenario_config, list_scenarios

router = APIRouter(prefix="/api")


def _mgr(request: Request) -> SimulationManager:
    return request.app.state.sim_manager


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "system": "EIDOLON"}


@router.get("/scenarios")
def get_scenarios() -> dict[str, Any]:
    return {"scenarios": list_scenarios()}


@router.get("/experiments")
def list_experiments(request: Request) -> dict[str, Any]:
    mgr = _mgr(request)
    return {
        "active_experiment_id": mgr.active_experiment_id,
        "experiments": mgr.repo.list_experiments(),
    }


@router.post("/experiments")
async def create_experiment(body: CreateExperimentRequest, request: Request) -> dict[str, Any]:
    mgr = _mgr(request)
    if mgr.active_experiment_id:
        await mgr.pause(mgr.active_experiment_id)
    try:
        cfg = get_scenario_config(body.scenario_id)
    except KeyError:
        cfg = ExperimentConfig()
    cfg_dict = cfg.to_dict()
    cfg_dict.update(body.config_overrides)
    if body.name:
        cfg_dict["name"] = body.name
    if body.description is not None:
        cfg_dict["description"] = body.description
    if body.seed is not None:
        cfg_dict["seed"] = body.seed
    if body.population_size is not None:
        cfg_dict["population_size"] = body.population_size
    if body.duration_ticks is not None:
        cfg_dict["duration_ticks"] = body.duration_ticks

    new_cfg = ExperimentConfig.from_dict(cfg_dict)
    eng = mgr.create_experiment(new_cfg)
    return {"experiment": mgr.repo.get_experiment(eng.experiment_id), "summary": eng.state_summary()}


@router.post("/experiments/import")
async def import_experiment(body: ImportExperimentRequest, request: Request) -> dict[str, Any]:
    mgr = _mgr(request)
    if mgr.active_experiment_id:
        await mgr.pause(mgr.active_experiment_id)
    cfg_dict = dict(body.config)
    cfg_dict["name"] = body.name
    eng = mgr.create_experiment(ExperimentConfig.from_dict(cfg_dict))
    return {"experiment": mgr.repo.get_experiment(eng.experiment_id), "summary": eng.state_summary()}


@router.post("/experiments/{experiment_id}/select")
async def select_experiment(experiment_id: str, request: Request) -> dict[str, Any]:
    mgr = _mgr(request)
    if mgr.active_experiment_id and mgr.active_experiment_id != experiment_id:
        await mgr.pause(mgr.active_experiment_id)
    try:
        eng = mgr.select_experiment(experiment_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"active_experiment_id": eng.experiment_id, "summary": eng.state_summary()}


@router.post("/experiments/{experiment_id}/duplicate")
def duplicate_experiment(experiment_id: str, body: DuplicateExperimentRequest, request: Request) -> dict[str, Any]:
    mgr = _mgr(request)
    try:
        eng = mgr.duplicate_experiment(experiment_id, new_name=body.name, seed=body.seed)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"experiment": mgr.repo.get_experiment(eng.experiment_id), "summary": eng.state_summary()}


@router.delete("/experiments/{experiment_id}")
async def delete_experiment(experiment_id: str, request: Request) -> dict[str, Any]:
    mgr = _mgr(request)
    await mgr.pause(experiment_id)
    mgr.engines.pop(experiment_id, None)
    mgr.repo.delete_experiment(experiment_id)
    if mgr.active_experiment_id == experiment_id:
        mgr.active_experiment_id = None
        mgr.ensure_default_experiment()
    return {"deleted": experiment_id, "active_experiment_id": mgr.active_experiment_id}


@router.get("/simulation/state")
def get_simulation_state(request: Request) -> dict[str, Any]:
    mgr = _mgr(request)
    eng = mgr.ensure_default_experiment()
    return {
        "status": mgr.run_states.get(eng.experiment_id, "paused"),
        "tick_interval_ms": int(mgr.tick_interval_sec * 1000),
        "summary": eng.state_summary(),
        "locations": [loc.to_dict() for loc in eng.world.locations.values()],
        "institutions": eng.institutions.active_list(),
        "communities": [c.to_dict() for c in eng.network.communities.values()],
        "recent_events": eng.events.recent_list(limit=60),
    }


@router.post("/simulation/run")
async def run_simulation(body: RunSimulationRequest, request: Request) -> dict[str, Any]:
    mgr = _mgr(request)
    eid = await mgr.start_running(body.experiment_id, tick_interval_ms=body.tick_interval_ms)
    return {"status": "running", "experiment_id": eid}


@router.post("/simulation/pause")
async def pause_simulation(request: Request) -> dict[str, Any]:
    mgr = _mgr(request)
    await mgr.pause()
    eng = mgr.ensure_default_experiment()
    return {"status": mgr.run_states.get(eng.experiment_id, "paused"), "tick": eng.clock.tick}


@router.post("/simulation/stop")
async def stop_simulation(request: Request) -> dict[str, Any]:
    mgr = _mgr(request)
    await mgr.stop()
    eng = mgr.ensure_default_experiment()
    return {"status": mgr.run_states.get(eng.experiment_id, "stopped"), "tick": eng.clock.tick}


@router.post("/simulation/step")
def step_simulation(body: StepSimulationRequest, request: Request) -> dict[str, Any]:
    mgr = _mgr(request)
    rows = mgr.step_once(body.experiment_id, steps=body.steps)
    eng = mgr.get_engine(body.experiment_id)
    return {
        "status": mgr.run_states.get(eng.experiment_id, "paused"),
        "steps_executed": len(rows),
        "summary": eng.state_summary(),
        "latest_metric": rows[-1] if rows else None,
    }


@router.patch("/simulation/config")
def patch_live_config(body: LiveConfigPatchRequest, request: Request) -> dict[str, Any]:
    mgr = _mgr(request)
    eng = mgr.ensure_default_experiment()
    data = body.model_dump(exclude_none=True)
    updated: dict[str, Any] = {}
    if "tick_interval_ms" in data:
        mgr.tick_interval_sec = max(0.01, data.pop("tick_interval_ms") / 1000.0)
        updated["tick_interval_ms"] = mgr.tick_interval_sec * 1000.0
    for k, v in data.items():
        if k == "env_event_probability":
            if hasattr(eng.environment, "event_probability"):
                setattr(eng.environment, "event_probability", v)
                updated[k] = v
            continue
        if hasattr(eng.config, k):
            setattr(eng.config, k, v)
            updated[k] = v
        if hasattr(eng.environment, k):
            setattr(eng.environment, k, v)
            updated[k] = v
    return {"updated": updated, "config": eng.config.to_dict()}


@router.get("/agents")
def list_agents(
    request: Request,
    location_id: str | None = None,
    community_id: str | None = None,
    occupation: str | None = None,
    limit: int = Query(default=250, ge=1, le=2000),
) -> dict[str, Any]:
    mgr = _mgr(request)
    eng = mgr.ensure_default_experiment()
    prices = eng.economy.prices
    out = []
    for aid in sorted(eng.agents.keys()):
        ag = eng.agents[aid]
        if not ag.alive:
            continue
        if location_id and ag.location_id != location_id:
            continue
        if community_id and ag.community_id != community_id:
            continue
        if occupation and ag.occupation != occupation:
            continue
        out.append(ag.to_summary_dict(prices))
        if len(out) >= limit:
            break
    return {"total": len(eng.agents), "agents": out}


@router.get("/agents/{agent_id}")
def get_agent_detail(agent_id: str, request: Request) -> dict[str, Any]:
    mgr = _mgr(request)
    eng = mgr.ensure_default_experiment()
    ag = eng.agents.get(agent_id)
    if not ag:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")

    rels = [
        e.to_dict()
        for e in eng.network.edges.values()
        if e.source_id == agent_id or e.target_id == agent_id
    ]
    rels.sort(key=lambda r: r["weight"], reverse=True)
    inst = eng.institutions.get_for_agent(agent_id)
    return {
        "agent": ag.to_detail_dict(eng.economy.prices),
        "relationships": rels[:30],
        "institution": inst.to_dict() if inst else None,
        "events": eng.events.for_agent(agent_id, limit=40),
    }


@router.get("/social/network")
def get_social_network(
    request: Request,
    max_edges: int = Query(default=400, ge=10, le=2000),
) -> dict[str, Any]:
    mgr = _mgr(request)
    eng = mgr.ensure_default_experiment()
    net_stats = compute_network_analytics(eng)

    nodes = [
        {
            "agent_id": ag.agent_id,
            "name": ag.name,
            "location_id": ag.location_id,
            "community_id": ag.community_id,
            "reputation": round(ag.reputation, 3),
            "occupation": ag.occupation,
            "x": eng.world.locations[ag.location_id].x,
            "y": eng.world.locations[ag.location_id].y,
        }
        for ag in eng.agents.values()
        if ag.alive
    ]
    edges = sorted(
        (e.to_dict() for e in eng.network.edges.values()),
        key=lambda e: (e["interaction_count"], e["weight"]),
        reverse=True,
    )[:max_edges]

    return {
        "analytics": net_stats,
        "nodes": nodes,
        "edges": edges,
        "communities": [c.to_dict() for c in eng.network.communities.values()],
        "institutions": eng.institutions.active_list(),
    }


@router.get("/analytics/metrics")
def get_metrics(request: Request) -> dict[str, Any]:
    mgr = _mgr(request)
    eng = mgr.ensure_default_experiment()
    return {
        "experiment_id": eng.experiment_id,
        "metrics": eng.metrics_history,
        "wealth_distribution": compute_wealth_distribution(eng),
    }


@router.get("/analytics/emergence")
def get_emergence(request: Request) -> dict[str, Any]:
    mgr = _mgr(request)
    eng = mgr.ensure_default_experiment()
    patterns = detect_emergent_patterns(eng)
    return {
        "tick": eng.clock.tick,
        "patterns": patterns,
        "network": compute_network_analytics(eng),
        "wealth": compute_wealth_distribution(eng),
    }


@router.post("/analytics/compare")
def compare_experiments(body: CompareSavedRequest, request: Request) -> dict[str, Any]:
    mgr = _mgr(request)
    if body.mode == "controlled_trials":
        cfg_a = ExperimentConfig.from_dict(body.config_a or get_scenario_config("scarcity_experiment").to_dict())
        cfg_b = ExperimentConfig.from_dict(body.config_b or get_scenario_config("cooperation_experiment").to_dict())
        return run_controlled_comparison(cfg_a, cfg_b, seeds=body.seeds, ticks=body.ticks)

    if not body.experiment_a_id or not body.experiment_b_id:
        raise HTTPException(status_code=400, detail="Provide experiment_a_id and experiment_b_id")

    exp_a = mgr.repo.get_experiment(body.experiment_a_id)
    exp_b = mgr.repo.get_experiment(body.experiment_b_id)
    if not exp_a or not exp_b:
        raise HTTPException(status_code=404, detail="One or both experiments not found")

    hist_a = (
        mgr.engines[body.experiment_a_id].metrics_history
        if body.experiment_a_id in mgr.engines
        else mgr.repo.get_metrics(body.experiment_a_id)
    )
    hist_b = (
        mgr.engines[body.experiment_b_id].metrics_history
        if body.experiment_b_id in mgr.engines
        else mgr.repo.get_metrics(body.experiment_b_id)
    )
    return compare_saved_histories(exp_a, hist_a, exp_b, hist_b)


@router.post("/analytics/export")
def export_experiment(request: Request) -> dict[str, Any]:
    mgr = _mgr(request)
    eng = mgr.ensure_default_experiment()
    paths = export_experiment_bundle(eng)
    return {
        "exported": True,
        "files": paths,
        "json_url": f"/api/analytics/report/{Path(paths['json_path']).name}",
        "csv_url": f"/api/analytics/report/{Path(paths['csv_path']).name}",
        "chart_url": f"/api/analytics/report/{Path(paths['chart_path']).name}",
    }


@router.get("/analytics/report/{filename}")
def download_report(filename: str) -> FileResponse:
    safe_name = Path(filename).name
    for folder in (EXPORTS_DIR, REPORTS_DIR):
        target = folder / safe_name
        if target.exists():
            return FileResponse(path=target, filename=safe_name)
    raise HTTPException(status_code=404, detail="Report file not found")


@router.get("/snapshots")
def list_snapshots(request: Request, experiment_id: str | None = None) -> dict[str, Any]:
    mgr = _mgr(request)
    return {"snapshots": mgr.repo.list_snapshots(experiment_id)}


@router.post("/snapshots")
def create_snapshot(body: SaveSnapshotRequest, request: Request) -> dict[str, Any]:
    mgr = _mgr(request)
    eng = mgr.ensure_default_experiment()
    snap = mgr.repo.save_snapshot(eng, label=body.label)
    return {"snapshot": snap}


@router.post("/snapshots/{snapshot_id}/restore")
async def restore_snapshot(snapshot_id: str, request: Request) -> dict[str, Any]:
    mgr = _mgr(request)
    if mgr.active_experiment_id:
        await mgr.pause(mgr.active_experiment_id)
    try:
        eng = mgr.repo.load_snapshot(snapshot_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    mgr.engines[eng.experiment_id] = eng
    mgr.active_experiment_id = eng.experiment_id
    mgr.run_states[eng.experiment_id] = "paused"
    mgr.repo.sync_world_and_agents(eng)
    return {"restored": True, "summary": eng.state_summary()}


@router.post("/backups")
def create_db_backup(request: Request) -> dict[str, Any]:
    mgr = _mgr(request)
    path = mgr.db.backup(label="researcher")
    return {"backup_path": str(path), "filename": path.name}


@router.get("/diagnostics")
def get_diagnostics(request: Request) -> dict[str, Any]:
    mgr = _mgr(request)
    eng = mgr.ensure_default_experiment()
    proc = psutil.Process(os.getpid())
    mem_mb = proc.memory_info().rss / (1024 * 1024)
    cpu_pct = proc.cpu_percent(interval=None)
    return {
        "tick": eng.clock.tick,
        "status": mgr.run_states.get(eng.experiment_id, "paused"),
        "last_tick_ms": round(eng.last_tick_ms, 3),
        "avg_tick_ms": round(eng.avg_tick_ms, 3),
        "theoretical_max_tps": round(1000.0 / max(0.1, eng.avg_tick_ms), 1) if eng.avg_tick_ms > 0 else 0.0,
        "memory_mb": round(mem_mb, 2),
        "cpu_percent": round(cpu_pct, 2),
        "database": mgr.db.stats(),
        "events_emitted_total": eng.events.total_emitted,
        "active_subsystems": {
            "agent_cognition": True,
            "tabular_q_learning": True,
            "social_learning": True,
            "episodic_semantic_procedural_memory": True,
            "social_network_trust": True,
            "cultural_transmission": True,
            "institutions": eng.config.institutions_enabled,
            "emergence_detector": True,
            "external_ai_dependencies": False,
        },
        "error_logs": mgr.error_logs[-20:],
    }
