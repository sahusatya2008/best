"""Tests for SimulationClock, SeededRNG, WorldGrid, Resources, Economy, and Simulation Invariants."""

from eidolon.core.clock import SimulationClock
from eidolon.core.engine import ExperimentConfig, SimulationEngine
from eidolon.core.rng import SeededRNG
from eidolon.world.economy import EconomicLedger
from eidolon.world.grid import WorldGrid
from eidolon.world.resources import RESOURCE_TYPES, ResourceStock, transfer_resource


def test_clock_and_rng_serialization():
    clock = SimulationClock()
    for _ in range(60):
        clock.advance()
    assert clock.tick == 60
    assert clock.day == 15
    assert clock.season == "summer"

    rng1 = SeededRNG(99)
    _ = [rng1.random() for _ in range(10)]
    state = rng1.get_state()
    rng2 = SeededRNG.from_state(state)
    assert [rng1.random() for _ in range(5)] == [rng2.random() for _ in range(5)]


def test_transactional_resources_never_negative():
    stock = ResourceStock("food", quantity=3.0, max_capacity=10.0, regen_rate=1.0)
    taken = stock.withdraw(100.0)
    assert taken == 3.0
    assert stock.quantity == 0.0

    inv_a = {r: 1.0 for r in RESOURCE_TYPES}
    inv_b = {r: 0.0 for r in RESOURCE_TYPES}
    moved = transfer_resource(inv_a, inv_b, "food", 5.0)
    assert moved == 1.0
    assert inv_a["food"] == 0.0
    assert inv_b["food"] == 1.0


def test_world_connectivity_and_economy_trade():
    rng = SeededRNG(42)
    world = WorldGrid.generate(rng, num_locations=12)
    ids = list(world.locations.keys())
    for dst in ids[1:]:
        hop = world.next_hop(ids[0], dst)
        assert hop != ids[0]

    ledger = EconomicLedger()
    buyer = {r: 0.2 for r in RESOURCE_TYPES}
    buyer["raw_materials"] = 6.0
    seller = {r: 0.2 for r in RESOURCE_TYPES}
    seller["food"] = 6.0
    res = ledger.execute_bilateral_trade(buyer, seller, "food", "raw_materials", desired_amount=2.0)
    assert res is not None
    assert buyer["food"] > 0.2
    assert seller["raw_materials"] > 0.2
    assert all(v >= 0.0 for v in buyer.values())
    assert all(v >= 0.0 for v in seller.values())


def test_simulation_invariants_50_ticks():
    cfg = ExperimentConfig(population_size=40, seed=7, duration_ticks=50)
    eng = SimulationEngine("inv_test", cfg)
    for t in range(1, 51):
        m = eng.step()
        assert m["tick"] == t
        assert eng.clock.tick == t

    seen_ids = set()
    for ag in eng.agents.values():
        assert ag.agent_id not in seen_ids
        seen_ids.add(ag.agent_id)
        assert ag.location_id in eng.world.locations
        for qty in ag.resources.values():
            assert qty >= 0.0
        for val in ag.needs.to_dict().values():
            assert 0.0 <= val <= 1.0
    for loc in eng.world.locations.values():
        for st in loc.resources.values():
            assert 0.0 <= st.quantity <= st.max_capacity + 1e-6
    for edge in eng.network.edges.values():
        assert edge.source_id in eng.agents and edge.target_id in eng.agents
