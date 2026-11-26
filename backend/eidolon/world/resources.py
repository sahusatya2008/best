"""Resource definitions, transactional stock management, and invariant guards."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

RESOURCE_TYPES: tuple[str, ...] = (
    "food",
    "water",
    "raw_materials",
    "tools",
    "knowledge",
    "energy",
)

BASE_RESOURCE_VALUES: dict[str, float] = {
    "food": 1.2,
    "water": 1.0,
    "raw_materials": 1.1,
    "tools": 2.4,
    "knowledge": 2.0,
    "energy": 1.3,
}


@dataclass
class ResourceStock:
    """Represents a bounded, regenerating resource deposit at a world location."""

    resource_type: str
    quantity: float
    max_capacity: float
    regen_rate: float

    def __post_init__(self) -> None:
        self.quantity = max(0.0, min(self.max_capacity, float(self.quantity)))
        self.max_capacity = max(0.0, float(self.max_capacity))
        self.regen_rate = max(0.0, float(self.regen_rate))

    def regenerate(self, multiplier: float = 1.0) -> float:
        """Logistic-modulated regeneration up to max_capacity."""
        if self.max_capacity <= 0.0 or self.regen_rate <= 0.0:
            return 0.0
        headroom = max(0.0, 1.0 - (self.quantity / self.max_capacity))
        delta = self.regen_rate * multiplier * (0.35 + 0.65 * headroom)
        before = self.quantity
        self.quantity = min(self.max_capacity, self.quantity + delta)
        return self.quantity - before

    def withdraw(self, amount: float) -> float:
        """Transactional withdrawal; never returns more than available or goes negative."""
        if amount <= 0.0:
            return 0.0
        taken = min(self.quantity, float(amount))
        self.quantity = max(0.0, self.quantity - taken)
        return taken

    def deposit(self, amount: float) -> float:
        if amount <= 0.0:
            return 0.0
        before = self.quantity
        self.quantity = min(self.max_capacity, self.quantity + float(amount))
        return self.quantity - before

    def to_dict(self) -> dict[str, float | str]:
        return {
            "resource_type": self.resource_type,
            "quantity": round(self.quantity, 4),
            "max_capacity": round(self.max_capacity, 4),
            "regen_rate": round(self.regen_rate, 4),
        }

    def to_snapshot_dict(self) -> dict[str, float | str]:
        return {
            "resource_type": self.resource_type,
            "quantity": self.quantity,
            "max_capacity": self.max_capacity,
            "regen_rate": self.regen_rate,
        }

    @classmethod
    def from_dict(cls, data: dict) -> ResourceStock:
        return cls(
            resource_type=data["resource_type"],
            quantity=float(data["quantity"]),
            max_capacity=float(data["max_capacity"]),
            regen_rate=float(data["regen_rate"]),
        )


def empty_inventory() -> Dict[str, float]:
    return {r: 0.0 for r in RESOURCE_TYPES}


def transfer_resource(
    sender_inv: dict[str, float],
    receiver_inv: dict[str, float],
    resource_type: str,
    amount: float,
) -> float:
    """Atomic non-negative resource transfer between two inventories."""
    if amount <= 0.0 or resource_type not in sender_inv:
        return 0.0
    available = max(0.0, sender_inv.get(resource_type, 0.0))
    actual = min(available, float(amount))
    if actual <= 0.0:
        return 0.0
    sender_inv[resource_type] = available - actual
    receiver_inv[resource_type] = receiver_inv.get(resource_type, 0.0) + actual
    return actual


def inventory_wealth(inv: dict[str, float], prices: dict[str, float] | None = None) -> float:
    p = prices or BASE_RESOURCE_VALUES
    return sum(max(0.0, inv.get(r, 0.0)) * p.get(r, 1.0) for r in RESOURCE_TYPES)
