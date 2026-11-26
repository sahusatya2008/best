"""Security hardening tests for loopback-only access and live config mapping."""

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from eidolon.core.runner import SimulationManager
from eidolon.main import app
from eidolon.persistence.database import Database


def _isolated_client(tmp_path):
    """Return a TestClient whose lifespan state is replaced with a temp DB manager."""
    client = TestClient(app)
    mgr = SimulationManager(db=Database(tmp_path / "security_test.db"))
    mgr.ensure_default_experiment()
    return client, mgr


def test_cors_allows_loopback_origin_and_blocks_external(tmp_path):
    client, mgr = _isolated_client(tmp_path)
    with client:
        app.state.sim_manager = mgr

        allowed = client.get("/api/health", headers={"Origin": "http://127.0.0.1:5173"})
        assert allowed.status_code == 200
        assert allowed.headers.get("access-control-allow-origin") == "http://127.0.0.1:5173"
        assert allowed.headers.get("access-control-allow-credentials") == "true"

        blocked = client.get("/api/health", headers={"Origin": "https://evil.com"})
        assert blocked.status_code == 200
        assert "access-control-allow-origin" not in blocked.headers


def test_websocket_accepts_no_origin_and_loopback_origin(tmp_path):
    client, mgr = _isolated_client(tmp_path)
    with client:
        app.state.sim_manager = mgr

        with client.websocket_connect("/ws/simulation") as ws:
            assert ws.receive_json()["type"] == "initial_state"

        with client.websocket_connect("/ws/simulation", headers={"origin": "http://localhost:5173"}) as ws:
            assert ws.receive_json()["type"] == "initial_state"


def test_websocket_rejects_external_origin_with_policy_close(tmp_path):
    client, mgr = _isolated_client(tmp_path)
    with client:
        app.state.sim_manager = mgr

        with client.websocket_connect("/ws/simulation", headers={"origin": "https://evil.com"}) as ws:
            with pytest.raises(WebSocketDisconnect) as exc:
                ws.receive_json()
            assert exc.value.code == 1008


def test_live_config_patch_maps_environment_event_probability(tmp_path):
    client, mgr = _isolated_client(tmp_path)
    with client:
        app.state.sim_manager = mgr

        before = client.get("/api/simulation/state").json()["summary"]["environment"]["event_probability"]
        assert before != 0.137

        response = client.patch("/api/simulation/config", json={"env_event_probability": 0.137})
        assert response.status_code == 200
        assert response.json()["updated"]["env_event_probability"] == 0.137

        after = client.get("/api/simulation/state").json()["summary"]["environment"]["event_probability"]
        assert after == 0.137
