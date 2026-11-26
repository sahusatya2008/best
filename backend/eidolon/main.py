"""EIDOLON FastAPI application entrypoint with WebSocket streaming and static UI support."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlparse

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from eidolon.api.router import router
from eidolon.config import PROJECT_ROOT
from eidolon.core.runner import SimulationManager


@asynccontextmanager
async def lifespan(app: FastAPI):
    mgr = SimulationManager()
    mgr.ensure_default_experiment()
    app.state.sim_manager = mgr
    yield
    for eid in list(mgr.running_tasks.keys()):
        await mgr.pause(eid)


app = FastAPI(
    title="EIDOLON",
    description="Autonomous Artificial Society & Computational Sociology Laboratory (100% Local, Zero External AI)",
    version="0.1.0",
    lifespan=lifespan,
)

# Offline-first: only loopback browsers may call the API cross-origin.
# Override with a comma-separated list if a local tool needs another origin.
ALLOWED_ORIGINS = [o.strip() for o in os.getenv("EIDOLON_ALLOWED_ORIGINS", "").split(",") if o.strip()]
LOCAL_ORIGIN_REGEX = r"^https?://(127\.0\.0\.1|localhost|\[::1\])(:\d+)?$"

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=None if ALLOWED_ORIGINS else LOCAL_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


def _origin_allowed(origin: str | None) -> bool:
    """Accept non-browser clients and loopback origins only (CSWSH defence)."""
    if not origin:
        return True
    if ALLOWED_ORIGINS:
        return origin in ALLOWED_ORIGINS
    parsed = urlparse(origin)
    host = (parsed.hostname or "").lower()
    return parsed.scheme in {"http", "https", "ws", "wss"} and host in {"127.0.0.1", "localhost", "::1"}

app.include_router(router)


@app.websocket("/ws/simulation")
async def simulation_websocket(websocket: WebSocket) -> None:
    if not _origin_allowed(websocket.headers.get("origin")):
        # Accept only to deliver a WebSocket policy-close (1008) to browsers.
        # No simulation state is sent before this check.
        await websocket.accept()
        await websocket.close(code=1008, reason="origin not allowed")
        return
    await websocket.accept()
    mgr: SimulationManager = app.state.sim_manager
    queue = mgr.subscribe()
    try:
        eng = mgr.ensure_default_experiment()
        await websocket.send_json(
            {
                "type": "initial_state",
                "status": mgr.run_states.get(eng.experiment_id, "paused"),
                "summary": eng.state_summary(),
                "locations": [loc.to_dict() for loc in eng.world.locations.values()],
            }
        )
        while True:
            msg = await queue.get()
            await websocket.send_json(msg)
    except WebSocketDisconnect:
        pass
    except Exception:
        raise
    finally:
        mgr.unsubscribe(queue)


FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="static")
