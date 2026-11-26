"""Structured proximity-based communication protocol (no LLM/natural-language generation)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from eidolon.agent.cognition import Agent
    from eidolon.social.relationships import SocialNetwork


@dataclass
class StructuredMessage:
    tick: int
    sender_id: str
    receiver_id: str
    msg_type: str  # info_resource | request_help | offer_trade | agreement | disagreement
    payload: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "tick": self.tick,
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "msg_type": self.msg_type,
            "payload": dict(self.payload),
        }


def exchange_information(
    sender: Agent,
    receiver: Agent,
    network: SocialNetwork,
    tick: int,
    local_stocks: dict[str, float],
) -> StructuredMessage:
    """Transmit resource knowledge and beliefs modulated by interpersonal trust."""
    trust = network.get_trust(receiver.agent_id, sender.agent_id, default=0.5)
    # Sender shares best known resource or belief
    best_res = max(local_stocks.items(), key=lambda kv: kv[1])[0] if local_stocks else "food"
    sender_belief = sender.beliefs.get("world.cooperation_payoff")
    shared_val = sender_belief.value if sender_belief else 0.5

    # Receiver integrates message proportional to trust
    if trust >= 0.35:
        receiver.memory.update_semantic(
            key=f"known_rich_loc.{best_res}",
            value=sender.location_id,
            confidence=min(0.95, 0.35 + 0.55 * trust),
            tick=tick,
        )
        if "world.cooperation_payoff" in receiver.beliefs:
            receiver.beliefs["world.cooperation_payoff"].update(shared_val, tick, weight=0.15 * trust)
        msg_type = "agreement" if trust >= 0.65 else "info_resource"
    else:
        msg_type = "disagreement"

    receiver.needs.adjust("social_connection", 0.08)
    sender.needs.adjust("social_connection", 0.09)
    network.record_interaction(sender.agent_id, receiver.agent_id, "communicate", tick)

    return StructuredMessage(
        tick=tick,
        sender_id=sender.agent_id,
        receiver_id=receiver.agent_id,
        msg_type=msg_type,
        payload={
            "resource_hint": best_res,
            "location_id": sender.location_id,
            "trust": round(trust, 3),
            "coop_belief": round(shared_val, 3),
        },
    )
