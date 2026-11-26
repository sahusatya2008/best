"""Deterministic seeded random number generator wrapper for reproducibility."""

from __future__ import annotations

import random
from typing import Any, Sequence, TypeVar

import numpy as np

T = TypeVar("T")


class SeededRNG:
    """Encapsulates both Python random.Random and NumPy Generator with full state serialization."""

    def __init__(self, seed: int = 42) -> None:
        self.seed = int(seed)
        self.py = random.Random(self.seed)
        self.np = np.random.default_rng(self.seed)

    def random(self) -> float:
        return self.py.random()

    def uniform(self, low: float, high: float) -> float:
        return self.py.uniform(low, high)

    def randint(self, low: int, high: int) -> int:
        return self.py.randint(low, high)

    def gauss(self, mu: float, sigma: float) -> float:
        return self.py.gauss(mu, sigma)

    def choice(self, seq: Sequence[T]) -> T:
        return self.py.choice(seq)

    def choices(self, population: Sequence[T], weights: Sequence[float], k: int = 1) -> list[T]:
        return self.py.choices(population, weights=weights, k=k)

    def shuffle(self, seq: list[Any]) -> None:
        self.py.shuffle(seq)

    def normal_clipped(self, mu: float, sigma: float, low: float = 0.0, high: float = 1.0) -> float:
        val = self.py.gauss(mu, sigma)
        return max(low, min(high, val))

    def get_state(self) -> dict[str, Any]:
        py_state = self.py.getstate()
        np_state = self.np.bit_generator.state
        return {
            "seed": self.seed,
            "py_version": py_state[0],
            "py_internal": list(py_state[1]),
            "py_gauss": py_state[2],
            "np_state": np_state,
        }

    @classmethod
    def from_state(cls, data: dict[str, Any]) -> SeededRNG:
        rng = cls(seed=int(data["seed"]))
        rng.py.setstate((data["py_version"], tuple(data["py_internal"]), data["py_gauss"]))
        rng.np.bit_generator.state = data["np_state"]
        return rng
