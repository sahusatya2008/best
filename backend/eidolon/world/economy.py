"""Experimental economy: supply/demand pricing, production, bilateral trade, and wealth inequality."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from eidolon.world.resources import (
    BASE_RESOURCE_VALUES,
    RESOURCE_TYPES,
    inventory_wealth,
    transfer_resource,
)


@dataclass
class EconomicLedger:
    """Tracks real supply, demand, exchange prices, trade volume, and wealth inequality."""

    prices: dict[str, float] = field(default_factory=lambda: dict(BASE_RESOURCE_VALUES))
    tick_trade_volume: float = 0.0
    total_trade_volume: float = 0.0
    total_trades: int = 0
    total_produced: float = 0.0
    total_consumed: float = 0.0

    def reset_tick_counters(self) -> None:
        self.tick_trade_volume = 0.0

    def update_market_prices(self, agent_inventories: list[dict[str, float]], population: int) -> None:
        """Compute scarcity-driven prices from actual aggregate stocks vs per-capita baseline demand."""
        if population <= 0:
            return
        baseline_per_agent = {
            "food": 3.0,
            "water": 3.0,
            "raw_materials": 2.0,
            "tools": 1.0,
            "knowledge": 1.5,
            "energy": 2.2,
        }
        for r in RESOURCE_TYPES:
            supply = sum(max(0.0, inv.get(r, 0.0)) for inv in agent_inventories)
            demand = population * baseline_per_agent[r]
            ratio = demand / max(1.0, supply)
            raw_price = BASE_RESOURCE_VALUES[r] * max(0.4, min(4.0, ratio))
            # Smooth adjustment to preserve price continuity
            self.prices[r] = round(0.75 * self.prices[r] + 0.25 * raw_price, 4)

    def execute_bilateral_trade(
        self,
        buyer_inv: dict[str, float],
        seller_inv: dict[str, float],
        wanted_resource: str,
        offered_resource: str,
        desired_amount: float = 1.5,
    ) -> dict[str, Any] | None:
        """Settles an atomic exchange between two agents using current exchange rates."""
        if wanted_resource == offered_resource:
            return None
        seller_avail = seller_inv.get(wanted_resource, 0.0)
        buyer_avail = buyer_inv.get(offered_resource, 0.0)
        if seller_avail < 0.5 or buyer_avail < 0.5:
            return None

        price_wanted = self.prices.get(wanted_resource, 1.0)
        price_offered = self.prices.get(offered_resource, 1.0)
        exchange_ratio = price_wanted / max(0.1, price_offered)

        qty_wanted = min(desired_amount, seller_avail * 0.6, buyer_avail / max(0.2, exchange_ratio) * 0.6)
        qty_offered = qty_wanted * exchange_ratio
        if qty_wanted < 0.25 or qty_offered < 0.25:
            return None

        moved_to_buyer = transfer_resource(seller_inv, buyer_inv, wanted_resource, qty_wanted)
        moved_to_seller = transfer_resource(buyer_inv, seller_inv, offered_resource, qty_offered)
        if moved_to_buyer <= 0.0 or moved_to_seller <= 0.0:
            return None

        value = moved_to_buyer * price_wanted
        self.tick_trade_volume += value
        self.total_trade_volume += value
        self.total_trades += 1
        return {
            "wanted_resource": wanted_resource,
            "offered_resource": offered_resource,
            "qty_wanted": round(moved_to_buyer, 4),
            "qty_offered": round(moved_to_seller, 4),
            "trade_value": round(value, 4),
        }

    def compute_gini(self, agent_inventories: list[dict[str, float]]) -> float:
        """Standard Gini coefficient over agent inventory wealth."""
        if len(agent_inventories) < 2:
            return 0.0
        wealths = np.array(
            [inventory_wealth(inv, self.prices) for inv in agent_inventories],
            dtype=np.float64,
        )
        total = float(np.sum(wealths))
        if total <= 1e-9:
            return 0.0
        sorted_w = np.sort(wealths)
        n = len(sorted_w)
        index = np.arange(1, n + 1, dtype=np.float64)
        gini = float(np.sum((2.0 * index - n - 1.0) * sorted_w) / (n * total))
        return max(0.0, min(1.0, gini))

    def to_dict(self) -> dict[str, Any]:
        return {
            "prices": dict(self.prices),
            "tick_trade_volume": round(self.tick_trade_volume, 4),
            "total_trade_volume": round(self.total_trade_volume, 4),
            "total_trades": self.total_trades,
            "total_produced": round(self.total_produced, 4),
            "total_consumed": round(self.total_consumed, 4),
        }

    def to_snapshot_dict(self) -> dict[str, Any]:
        return {
            "prices": dict(self.prices),
            "tick_trade_volume": self.tick_trade_volume,
            "total_trade_volume": self.total_trade_volume,
            "total_trades": self.total_trades,
            "total_produced": self.total_produced,
            "total_consumed": self.total_consumed,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EconomicLedger:
        # This method is used for UI-oriented snapshots that may contain rounded values.
        return cls(
            prices={k: float(v) for k, v in data.get("prices", BASE_RESOURCE_VALUES).items()},
            tick_trade_volume=float(data.get("tick_trade_volume", 0.0)),
            total_trade_volume=float(data.get("total_trade_volume", 0.0)),
            total_trades=int(data.get("total_trades", 0)),
            total_produced=float(data.get("total_produced", 0.0)),
            total_consumed=float(data.get("total_consumed", 0.0)),
        )

    @classmethod
    def from_snapshot_dict(cls, data: dict[str, Any]) -> EconomicLedger:
        # Preserve raw values without rounding for deterministic restoration.
        return cls(
            prices={k: float(v) for k, v in data.get("prices", BASE_RESOURCE_VALUES).items()},
            tick_trade_volume=float(data.get("tick_trade_volume", 0.0)),
            total_trade_volume=float(data.get("total_trade_volume", 0.0)),
            total_trades=int(data.get("total_trades", 0)),
            total_produced=float(data.get("total_produced", 0.0)),
            total_consumed=float(data.get("total_consumed", 0.0)),
        )
