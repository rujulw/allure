from __future__ import annotations

from fastapi import WebSocket

from app.game.state import Action, ActionType
from app.realtime.events import serialize_hand, serialize_table_snapshot
from app.realtime.manager import RealtimeManager
from app.realtime.schemas import CommandEnvelope
from app.table.exceptions import TableError


async def handle_socket_session(
    websocket: WebSocket,
    *,
    table_id: str,
    player_id: str,
    realtime_manager: RealtimeManager,
) -> None:
    try:
        await realtime_manager.send_snapshot(table_id, websocket, player_id)
        while True:
            raw_message = await websocket.receive_json()
            command = CommandEnvelope.model_validate(raw_message)
            await process_command(
                table_id=table_id,
                player_id=player_id,
                command=command,
                realtime_manager=realtime_manager,
            )
    finally:
        disconnected_player = realtime_manager.disconnect(table_id, websocket)
        if disconnected_player is not None and table_id in realtime_manager.table_manager.tables:
            try:
                realtime_manager.table_manager.disconnect_player(table_id, disconnected_player)
                await realtime_manager.broadcast_event(
                    table_id,
                    "table_state_updated",
                    lambda viewer_id: serialize_table_snapshot(
                        realtime_manager.table_manager.tables[table_id],
                        viewer_id,
                    ),
                    hand_id=(
                        realtime_manager.table_manager.tables[table_id].active_hand.hand_id
                        if realtime_manager.table_manager.tables[table_id].active_hand is not None
                        else None
                    ),
                )
            except TableError:
                pass


async def process_command(
    *,
    table_id: str,
    player_id: str,
    command: CommandEnvelope,
    realtime_manager: RealtimeManager,
) -> None:
    table_manager = realtime_manager.table_manager
    try:
        if command.type == "request_snapshot":
            await realtime_manager.send_snapshot(
                table_id,
                _connection_websocket(realtime_manager, table_id, player_id),
                player_id,
            )
            return

        if command.type == "join_table":
            table = table_manager.join_table(table_id, player_id)
            await realtime_manager.broadcast_event(
                table_id,
                "player_joined",
                lambda viewer_id: {
                    "player_id": player_id,
                    "snapshot": serialize_table_snapshot(table, viewer_id),
                },
            )
            return

        if command.type == "take_seat":
            seat_index = int(command.payload["seat_index"])
            buy_in = int(command.payload["buy_in"])
            table = table_manager.seat_player(table_id, player_id, seat_index=seat_index, buy_in=buy_in)
            await realtime_manager.broadcast_event(
                table_id,
                "player_seated",
                lambda viewer_id: {
                    "player_id": player_id,
                    "seat_index": seat_index,
                    "buy_in": buy_in,
                    "snapshot": serialize_table_snapshot(table, viewer_id),
                },
            )
            return

        if command.type == "leave_table":
            table = table_manager.leave_table(table_id, player_id)
            await realtime_manager.broadcast_event(
                table_id,
                "player_left",
                lambda viewer_id: {
                    "player_id": player_id,
                    "snapshot": serialize_table_snapshot(table, viewer_id),
                },
            )
            return

        if command.type == "rejoin_table":
            table = table_manager.rejoin_table(table_id, player_id)
            await realtime_manager.broadcast_event(
                table_id,
                "player_rejoined",
                lambda viewer_id: {
                    "player_id": player_id,
                    "snapshot": serialize_table_snapshot(table, viewer_id),
                },
            )
            return

        if command.type == "sit_out":
            table = table_manager.sit_out(
                table_id,
                player_id,
                sitting_out=bool(command.payload.get("sitting_out", True)),
            )
            await realtime_manager.broadcast_snapshot(table_id)
            return

        if command.type == "start_hand":
            table = table_manager.start_hand(table_id)
            hand_id = table.active_hand.hand_id if table.active_hand is not None else None
            await realtime_manager.broadcast_event(
                table_id,
                "hand_started",
                lambda viewer_id: {"snapshot": serialize_table_snapshot(table, viewer_id)},
                hand_id=hand_id,
            )
            await realtime_manager.broadcast_event(
                table_id,
                "cards_dealt",
                lambda viewer_id: {"hand": serialize_hand(table.active_hand, viewer_id)},
                hand_id=hand_id,
            )
            await realtime_manager.broadcast_event(
                table_id,
                "action_requested",
                lambda viewer_id: {"hand": serialize_hand(table.active_hand, viewer_id)},
                hand_id=hand_id,
            )
            return

        if command.type == "player_action":
            action_type = ActionType(command.payload["action_type"])
            amount = command.payload.get("amount")
            table_before = table_manager.tables[table_id]
            previous_street = table_before.active_hand.street if table_before.active_hand is not None else None
            table = table_manager.apply_action(
                table_id,
                Action(player_id=player_id, action_type=action_type, amount=amount),
            )
            hand = table.active_hand
            completed_hand_id = table.hand_number if hand is None else hand.hand_id
            await realtime_manager.broadcast_event(
                table_id,
                "action_applied",
                lambda viewer_id: {
                    "player_id": player_id,
                    "action_type": action_type.value,
                    "amount": amount,
                    "hand": serialize_hand(hand, viewer_id),
                },
                hand_id=completed_hand_id,
            )
            await realtime_manager.broadcast_event(
                table_id,
                "pot_updated",
                lambda viewer_id: {
                    "hand": serialize_hand(hand, viewer_id),
                    "snapshot": serialize_table_snapshot(table, viewer_id),
                },
                hand_id=completed_hand_id,
            )

            if hand is not None and previous_street is not None and hand.street != previous_street:
                await realtime_manager.broadcast_event(
                    table_id,
                    "street_advanced",
                    lambda viewer_id: {"hand": serialize_hand(hand, viewer_id)},
                    hand_id=hand.hand_id,
                )

            if hand is None:
                await realtime_manager.broadcast_event(
                    table_id,
                    "hand_ended",
                    lambda viewer_id: {"snapshot": serialize_table_snapshot(table, viewer_id)},
                    hand_id=completed_hand_id,
                )
            else:
                await realtime_manager.broadcast_event(
                    table_id,
                    "action_requested",
                    lambda viewer_id: {"hand": serialize_hand(hand, viewer_id)},
                    hand_id=hand.hand_id,
                )
            return
    except TableError as exc:
        await _send_error(
            realtime_manager=realtime_manager,
            table_id=table_id,
            player_id=player_id,
            message=str(exc),
        )
        return
    except (KeyError, ValueError) as exc:
        await _send_error(
            realtime_manager=realtime_manager,
            table_id=table_id,
            player_id=player_id,
            message=str(exc),
        )
        return


async def _send_error(
    *,
    realtime_manager: RealtimeManager,
    table_id: str,
    player_id: str,
    message: str,
) -> None:
    websocket = _connection_websocket(realtime_manager, table_id, player_id)
    sequence = realtime_manager._next_sequence(table_id)
    await websocket.send_json(
        {
            "type": "error",
            "table_id": table_id,
            "sequence": sequence,
            "hand_id": None,
            "payload": {"message": message},
        }
    )


def _connection_websocket(realtime_manager: RealtimeManager, table_id: str, player_id: str) -> WebSocket:
    room = realtime_manager._connections.get(table_id, [])
    for connection in room:
        if connection.player_id == player_id:
            return connection.websocket
    raise RuntimeError(f"No websocket connection found for {player_id} at {table_id}")
