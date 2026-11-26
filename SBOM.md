# Software Bill of Materials (SBOM) — EIDOLON

All dependencies are open-source, locally executed, and zero external AI/LLM inference services are included. Direct pinned dependencies are listed below; transitive packages are recorded in `frontend/package-lock.json` and the Python environment.

## Backend Python Dependencies (Direct pins in `pyproject.toml`)
| Package | Version | Purpose | License |
|---|---|---|---|
| fastapi | 0.115.6 | Local REST & WebSocket API server | MIT |
| uvicorn | 0.34.0 | ASGI server | BSD-3-Clause |
| pydantic | 2.10.4 | Schema validation | MIT |
| numpy | 2.2.1 | Numerical array & Gini/entropy math | BSD-3-Clause |
| scipy | 1.15.0 | Statistical tests (t-distribution CIs, paired t-tests) | BSD-3-Clause |
| networkx | 3.4.2 | Social network centrality, clustering, modularity communities | BSD-3-Clause |
| matplotlib | 3.10.0 | Offline scientific PNG report generation | PSF |
| psutil | 6.1.1 | Local CPU & memory diagnostics | BSD-3-Clause |
| websockets | 14.1 | Live tick telemetry streaming | BSD-3-Clause |
| httpx | 0.28.1 | FastAPI TestClient transport | BSD-3-Clause |
| pytest | 9.0.3 | Automated unit/integration/invariant tests | MIT |
| pytest-asyncio | 0.25.0 | Async test support | Apache-2.0 |

## Frontend JavaScript/TypeScript Dependencies (Direct pins in `frontend/package.json`)
| Package | Version | Purpose | License |
|---|---|---|---|
| react / react-dom | 18.3.1 | UI rendering | MIT |
| typescript | 5.7.2 | Static type safety | Apache-2.0 |
| vite | 6.4.5 | Build & dev server | MIT |
| three | 0.170.0 | WebGL 3D world rendering | MIT |
| @react-three/fiber | 8.17.10 | React Three.js renderer (InstancedMesh) | MIT |
| @react-three/drei | 9.122.0 | OrbitControls, Line, Text helpers | MIT |
| plotly.js-dist-min | 2.35.3 | Scientific time-series charts | MIT |
| zustand | 5.0.2 | Client state store | MIT |
| tailwindcss | 3.4.17 | Utility styling | MIT |
| postcss | 8.5.33 | CSS transformation and source-map safety | MIT |
| lucide-react | 0.468.0 | Technical iconography | ISC |
| vitest | 4.1.12 | Frontend component verification | MIT |
