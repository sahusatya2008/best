# EIDOLON Developer Guide

## Running Automated Tests
```bash
# Backend unit, invariant, learning, reproducibility, snapshot & API tests
.venv/bin/pytest -v

# Frontend Vitest component tests
npm --prefix frontend test

# Hardware performance benchmark
.venv/bin/python backend/tests/benchmark.py
```

## Extending EIDOLON
- **Adding an Action**: Add the action key to `ACTIONS` in `backend/eidolon/agent/learning.py`, add its factor scoring in `calculate_action_utility()` in `backend/eidolon/agent/reasoning.py`, and implement its transactional execution in `SimulationEngine.step()` in `backend/eidolon/core/engine.py`.
- **Adding a Scenario**: Add a new entry in `SCENARIO_DEFINITIONS` inside `backend/eidolon/scenarios/presets.py`.
- **Adding a Database Migration**: Create `002_<name>.sql` in `backend/eidolon/persistence/migrations/`. `Database` automatically tracks and applies ordered migrations on startup.
- **Zero External AI Rule**: Do not import or call external LLM SDKs or hosted inference APIs. All intelligence must remain locally computed and mathematically transparent.
