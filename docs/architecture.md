# EIDOLON Technical Architecture

## System Overview
EIDOLON cleanly separates deterministic simulation logic (`backend/eidolon/`) from scientific presentation (`frontend/src/`), linked via a local FastAPI REST + WebSocket API and backed by normalized SQLite persistence.

```text
                  EIDOLON
                     |
          APPLICATION INTERFACE (React + Vite + Three.js + Plotly)
                     |
             LOCAL API LAYER (FastAPI + WebSockets)
                     |
             SIMULATION CORE (Clock, SeededRNG, 12-Step Engine)
                     |
       +-------------+-------------+
       |             |             |
   AGENT ENGINE  WORLD ENGINE  SOCIAL ENGINE
       |             |             |
   MEMORY CORE   ENVIRONMENT   RELATIONSHIPS & TRUST
       |             |             |
   LEARNING      RESOURCES     COMMUNICATION
       |             |             |
   REASONING     ECONOMY       CULTURE & INSTITUTIONS
       |             |             |
       +-------------+-------------+
                     |
              EVENT PROCESSOR & ANALYTICS ENGINE
                     |
              PERSISTENCE CORE (SQLite WAL + Compressed Snapshots)
```

## Module Boundaries
- `eidolon.core`: `SimulationClock`, `SeededRNG` (Python `random` + NumPy Generator with full state serialization), `EventBus`, `SimulationEngine`, and `SimulationManager`.
- `eidolon.world`: `WorldGrid` (spatial graph, shortest-path routing, resource stocks), `ResourceStock` (transactional non-negative withdrawals/transfers), `EnvironmentState` (seasonal multipliers, regeneration, stochastic natural events), and `EconomicLedger` (scarcity pricing, bilateral trade, Gini).
- `eidolon.agent`: `Agent` cognitive model (`BigFiveTraits`, `AgentNeeds`, `AgentGoal`, `AgentBelief`), `AgentMemory` (4-layer working/episodic/semantic/procedural + cosine similarity retrieval + consolidation), `QLearningEngine` (tabular Q-learning + social learning + failure adaptation), and `reasoning` (`calculate_action_utility` + explainable decision records).
- `eidolon.social`: `SocialNetwork` (asymmetric trust updates, non-permanent edge decay, NetworkX community detection), `communication` (structured proximity packets), `culture` (trait transmission, norm adoption, inter-community L1 divergence), and `InstitutionRegistry` (organic trust-based formation, dues, redistribution, violations, dissolution).
- `eidolon.analytics`: `metrics` (NetworkX centrality/clustering, wealth shares, spatial entropy), `emergence` (windowed empirical trend & structural pattern detectors), `comparison` (multi-seed trials, sample variance, 95% t-distribution CIs, paired t-tests), and `reports` (JSON, CSV, Matplotlib PNG export).
- `eidolon.persistence`: SQLite connection manager with automatic SQL migrations (`001_initial.sql`), WAL mode, batched tick inserts, versioned compressed snapshots with SHA-256 verification, and DB backup/restore.
