"""Tests for social trust dynamics, relationships, cultural transmission, and rule-based institutions."""

from eidolon.agent.cognition import Agent
from eidolon.core.rng import SeededRNG
from eidolon.social.culture import attempt_cultural_transmission
from eidolon.social.institutions import InstitutionRegistry
from eidolon.social.relationships import SocialNetwork


def test_trust_asymmetry_and_non_permanent_relationships():
    net = SocialNetwork()
    # One casual interaction is not considered a persistent active edge (min_interactions=2)
    net.record_interaction("a", "b", "communicate", tick=1)
    assert len(net.active_edges(min_interactions=2)) == 0

    # Repeated cooperation builds friendship/active edge
    for t in range(2, 7):
        net.record_interaction("a", "b", "cooperate", tick=t)
    assert len(net.active_edges(min_interactions=2)) == 1
    high_trust = net.get_trust("a", "b")
    assert high_trust > 0.7

    # Competition reduces trust sharply
    net.record_interaction("a", "b", "compete", tick=8)
    assert net.get_trust("a", "b") < high_trust


def test_cultural_transmission_and_institution_lifecycle():
    rng = SeededRNG(42)
    agents = [Agent.spawn(i + 1, "loc_00", rng, personality_means={"agreeableness": 0.75}, personality_std=0.05) for i in range(6)]
    agents[0].cultural_traits["sharing_norm"] = "generous"
    agents[0].last_reward = 0.8
    agents[1].cultural_traits["sharing_norm"] = "hoarding"
    agents[1].last_reward = 0.1

    adopted = False
    for _ in range(30):
        res = attempt_cultural_transmission(agents[0], agents[1], trust=0.9, transmission_rate=0.9, rng=rng)
        if res and res[0] == "sharing_norm":
            adopted = True
            break
    assert adopted

    net = SocialNetwork()
    for i in range(len(agents)):
        for j in range(i + 1, len(agents)):
            for t in range(1, 5):
                net.record_interaction(agents[i].agent_id, agents[j].agent_id, "cooperate", tick=t)

    reg = InstitutionRegistry()
    created = reg.try_form_institutions({"loc_00": agents}, net, tick=10, enabled=True, min_trust_threshold=0.55)
    assert len(created) == 1
    inst = created[0]
    assert len(inst.members) == 6

    # Surplus contribution and redistribution
    agents[0].resources["food"] = 10.0
    agents[1].resources["food"] = 0.2
    agents[1].needs.nutrition = 0.25
    by_id = {a.agent_id: a for a in agents}
    reg.step_institutions(by_id, tick=11)
    assert agents[1].resources["food"] > 0.2

    # Repeated violations reduce stability and can dissolve institution
    for _ in range(25):
        reg.record_violation(agents[2].agent_id)
    events = reg.step_institutions(by_id, tick=12)
    assert not inst.active
    assert any(e["event_type"] == "institution_dissolved" for e in events)
