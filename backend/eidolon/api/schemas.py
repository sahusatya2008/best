"""Pydantic request/response schemas for the local EIDOLON API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class CreateExperimentRequest(BaseModel):
    scenario_id: str = "cooperation_experiment"
    name: str | None = None
    description: str | None = None
    seed: int | None = None
    population_size: int | None = Field(default=None, ge=5, le=10000)
    duration_ticks: int | None = Field(default=None, ge=10, le=50000)
    config_overrides: dict[str, Any] = Field(default_factory=dict)


class DuplicateExperimentRequest(BaseModel):
    name: str | None = None
    seed: int | None = None


class RunSimulationRequest(BaseModel):
    experiment_id: str | None = None
    tick_interval_ms: int = Field(default=100, ge=10, le=5000)


class StepSimulationRequest(BaseModel):
    experiment_id: str | None = None
    steps: int = Field(default=1, ge=1, le=1000)


class LiveConfigPatchRequest(BaseModel):
    learning_rate: float | None = Field(default=None, ge=0.01, le=0.95)
    discount_factor: float | None = Field(default=None, ge=0.1, le=0.99)
    exploration_rate: float | None = Field(default=None, ge=0.0, le=0.8)
    social_learning_prob: float | None = Field(default=None, ge=0.0, le=1.0)
    adaptation_speed: float | None = Field(default=None, ge=0.1, le=3.0)
    cooperation_reward: float | None = Field(default=None, ge=0.0, le=1.5)
    social_interaction_prob: float | None = Field(default=None, ge=0.0, le=1.0)
    cultural_transmission_rate: float | None = Field(default=None, ge=0.0, le=1.0)
    institutions_enabled: bool | None = None
    climate_severity: float | None = Field(default=None, ge=0.0, le=1.0)
    regeneration_scale: float | None = Field(default=None, ge=0.1, le=3.0)
    env_event_probability: float | None = Field(default=None, ge=0.0, le=0.5)
    tick_interval_ms: int | None = Field(default=None, ge=10, le=5000)


class SaveSnapshotRequest(BaseModel):
    label: str = "checkpoint"


class CompareSavedRequest(BaseModel):
    mode: str = "saved"  # saved | controlled_trials
    experiment_a_id: str | None = None
    experiment_b_id: str | None = None
    config_a: dict[str, Any] | None = None
    config_b: dict[str, Any] | None = None
    seeds: list[int] = Field(default_factory=lambda: [42, 101, 202])
    ticks: int = Field(default=60, ge=10, le=500)


class ImportExperimentRequest(BaseModel):
    name: str
    config: dict[str, Any]
