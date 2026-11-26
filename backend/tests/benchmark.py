"""Actual hardware performance benchmark for EIDOLON across population scales."""

from __future__ import annotations

import os
import time
import psutil

from eidolon.core.engine import ExperimentConfig, SimulationEngine


def run_benchmark(pop_sizes: list[int], ticks: int = 20) -> list[dict[str, float | int]]:
    proc = psutil.Process(os.getpid())
    results = []
    for pop in pop_sizes:
        cfg = ExperimentConfig(population_size=pop, seed=42, duration_ticks=ticks)
        t_init0 = time.perf_counter()
        eng = SimulationEngine(f"bench_{pop}", cfg)
        init_ms = (time.perf_counter() - t_init0) * 1000.0

        tick_times = []
        for _ in range(ticks):
            t0 = time.perf_counter()
            eng.step()
            tick_times.append((time.perf_counter() - t0) * 1000.0)

        rss_mb = proc.memory_info().rss / (1024 * 1024)
        mean_ms = sum(tick_times) / len(tick_times)
        max_ms = max(tick_times)
        tps = 1000.0 / max(0.01, mean_ms)
        row = {
            "population": pop,
            "ticks": ticks,
            "init_ms": round(init_ms, 2),
            "mean_tick_ms": round(mean_ms, 2),
            "max_tick_ms": round(max_ms, 2),
            "ticks_per_sec": round(tps, 2),
            "rss_mb": round(rss_mb, 2),
        }
        results.append(row)
        print(row)
    return results


if __name__ == "__main__":
    run_benchmark([100, 500, 1000, 5000], ticks=15)
