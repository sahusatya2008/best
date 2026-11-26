# Installation & Offline Operation Guide

## Requirements
- macOS (Apple Silicon M1/M2/M3+ or Intel), 8 GB+ RAM
- Python 3.11+ (tested on Python 3.12.13)
- Node.js 20+ & npm (tested on Node v26.0.0)

## Reproducible Installation
Run the automated setup script (requires internet only once during installation to fetch open-source Python/npm packages):
```bash
./install.sh
```
This script:
1. Creates `.venv` using Python 3.12 and installs pinned backend dependencies from `pyproject.toml`.
2. Installs pinned frontend dependencies in `frontend/package.json` and builds `frontend/dist`.

## Offline Execution
Once installed, **no internet connection is required**:
```bash
./eidolon.sh
```
Open `http://127.0.0.1:8000` in your browser.
- All cognitive computations, reinforcement learning, memory retrieval, social network analysis, and Matplotlib rendering run locally on your CPU.
- All experiment histories, events, and versioned snapshots are stored locally in `data/eidolon.db`.
- Backups can be created from **Scenarios & Snapshots → Backup DB** and saved into `data/backups/`.
