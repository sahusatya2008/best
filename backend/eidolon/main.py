"""EIDOLON FastAPI application entrypoint with WebSocket streaming and static UI support."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.websocket("/ws/simulation")
async def simulation_websocket(websocket: WebSocket) -> None:
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
        mgr.unsubscribe(queue)
    except Exception:
        mgr.unsubscribe(queue)


FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="static")
