"""Tests for SQLite persistence, snapshot restoration, all 8 scenarios, and FastAPI endpoints."""

from fastapi.testclient import TestClient

from eidolon.core.engine import ExperimentConfig, SimulationEngine
from eidolon.core.runner import SimulationManager
from eidolon.main import app
from eidolon.persistence.database import Database
from eidolon.persistence.repository import ExperimentRepository
from eidolon.scenarios.presets import get_scenario_config, list_scenarios


def test_snapshot_save_and_exact_continuation(tmp_path):
    db = Database(tmp_path / "test_eidolon.db")
    repo = ExperimentRepository(db)

    cfg = ExperimentConfig(population_size=25, seed=77, duration_ticks=40)
    eng = SimulationEngine("snap_exp", cfg)
    repo.create_experiment_record(eng)

    for _ in range(15):
        eng.step()
    snap = repo.save_snapshot(eng, label="mid_run")

    # Continue original engine 10 more ticks
    for _ in range(10):
        eng.step()

    # Restore snapshot and advance 10 ticks: must match identically
    restored = repo.load_snapshot(snap["snapshot_id"])
    assert restored.clock.tick == 15
    for _ in range(10):
        restored.step()

    assert restored.metrics_history == eng.metrics_history
    for aid in eng.agents:
        assert restored.agents[aid].last_action == eng.agents[aid].last_action
        assert abs(restored.agents[aid].cumulative_reward - eng.agents[aid].cumulative_reward) < 1e-9

    backup_file = db.backup(label="unit")
    assert backup_file.exists()


def test_all_eight_scenarios_run():
    scenarios = list_scenarios()
    assert len(scenarios) == 8
    for sc in scenarios:
        cfg = get_scenario_config(sc["scenario_id"])
        cfg.population_size = 20
        eng = SimulationEngine(f"sc_{sc['scenario_id']}", cfg)
        m = eng.step()
        assert m["population"] == 20


def test_fastapi_endpoints_end_to_end(tmp_path, monkeypatch):
    db = Database(tmp_path / "api_test.db")
    mgr = SimulationManager(db=db)
    app.state.sim_manager = mgr
    mgr.ensure_default_experiment()

    with TestClient(app) as client:
        # Override lifespan manager with isolated temp DB
        app.state.sim_manager = mgr

        r = client.get("/api/health")
        assert r.status_code == 200
        assert r.json()["system"] == "EIDOLON"

        r = client.get("/api/scenarios")
        assert len(r.json()["scenarios"]) == 8

        r = client.post("/api/experiments", json={"scenario_id": "trust_experiment", "population_size": 24, "seed": 55})
        assert r.status_code == 200
        exp_id = r.json()["experiment"]["id"]

        r = client.post("/api/simulation/step", json={"experiment_id": exp_id, "steps": 12})
        assert r.status_code == 200
        assert r.json()["summary"]["clock"]["tick"] == 12

        r = client.get("/api/agents")
        agents = r.json()["agents"]
        assert len(agents) == 24

        r = client.get(f"/api/agents/{agents[0]['agent_id']}")
        assert r.status_code == 200
        assert "last_explanation" in r.json()["agent"]
        assert "decision_factors" in r.json()["agent"]["last_explanation"]

        r = client.get("/api/analytics/emergence")
        assert r.status_code == 200
        assert len(r.json()["patterns"]) >= 5

        r = client.get("/api/social/network")
        assert r.status_code == 200
        assert len(r.json()["nodes"]) == 24

        r = client.post("/api/snapshots", json={"label": "api_chk"})
        snap_id = r.json()["snapshot"]["snapshot_id"]

        r = client.post("/api/simulation/step", json={"steps": 5})
        assert r.json()["summary"]["clock"]["tick"] == 17

        r = client.post(f"/api/snapshots/{snap_id}/restore")
        assert r.status_code == 200
        assert r.json()["summary"]["clock"]["tick"] == 12

        r = client.get("/api/diagnostics")
        assert r.status_code == 200
        assert r.json()["active_subsystems"]["external_ai_dependencies"] is False
