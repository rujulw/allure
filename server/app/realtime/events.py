from __future__ import annotations

from app.game.state import HandState, LegalAction
from app.realtime.schemas import EventEnvelope
from app.table.state import SeatState, TableState


def serialize_seat(seat: SeatState | None) -> dict | None:
    if seat is None:
        return None
    return {
        "seat_index": seat.seat_index,
        "player_id": seat.player_id,
        "stack": seat.stack,
        "connected": seat.connected,
        "sitting_out": seat.sitting_out,
        "pending_leave": seat.pending_leave,
        "eligible_for_next_hand": seat.eligible_for_next_hand,
    }


def serialize_legal_action(action: LegalAction) -> dict:
    return {
        "action_type": action.action_type.value,
        "amount": action.amount,
        "min_amount": action.min_amount,
        "max_amount": action.max_amount,
        "call_amount": action.call_amount,
    }


def serialize_hand(hand: HandState | None, viewer_id: str | None) -> dict | None:
    if hand is None:
        return None

    visible_hole_cards: dict[str, list[str]] = {}
    for player in hand.players:
        if hand.phase.value == "complete" or player.player_id == viewer_id:
            visible_hole_cards[player.player_id] = [str(card) for card in player.hole_cards]

    current_actor_id = hand.current_actor.player_id if hand.current_actor is not None else None
    legal_actions = []
    if viewer_id is not None and current_actor_id == viewer_id:
        legal_actions = [serialize_legal_action(action) for action in hand.legal_actions]

    return {
        "hand_id": hand.hand_id,
        "phase": hand.phase.value,
        "street": hand.street.value,
        "community_cards": [str(card) for card in hand.community_cards],
        "pot": hand.pot,
        "pots": [
            {"amount": pot.amount, "eligible_player_ids": list(pot.eligible_player_ids)}
            for pot in hand.pots
        ],
        "current_actor_player_id": current_actor_id,
        "legal_actions": legal_actions,
        "winner_ids": hand.winner_ids,
        "payouts": hand.payouts,
        "visible_hole_cards": visible_hole_cards,
    }


def serialize_table_snapshot(table: TableState, viewer_id: str | None) -> dict:
    return {
        "table_id": table.table_id,
        "phase": table.phase.value,
        "hand_number": table.hand_number,
        "max_seats": table.max_seats,
        "blind_structure": {
            "small_blind": table.blind_structure.small_blind,
            "big_blind": table.blind_structure.big_blind,
        },
        "min_buy_in": table.min_buy_in,
        "max_buy_in": table.max_buy_in,
        "dealer_button_index": table.dealer_button_index,
        "waiting_player_ids": sorted(table.waiting_player_ids),
        "seats": [serialize_seat(seat) for seat in table.seats],
        "active_hand": serialize_hand(table.active_hand, viewer_id),
    }


def build_event(
    *,
    event_type: str,
    table_id: str,
    sequence: int,
    payload: dict,
    hand_id: int | None = None,
) -> EventEnvelope:
    return EventEnvelope(
        type=event_type,
        table_id=table_id,
        sequence=sequence,
        hand_id=hand_id,
        payload=payload,
    )
