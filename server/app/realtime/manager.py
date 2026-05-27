from __future__ import annotations

from dataclasses import dataclass

from fastapi import WebSocket

from app.realtime.events import build_event, serialize_table_snapshot
from app.table.manager import TableManager


@dataclass
class LiveConnection:
    player_id: str
    websocket: WebSocket


class RealtimeManager:
    def __init__(self, table_manager: TableManager):
        self.table_manager = table_manager
        self._connections: dict[str, list[LiveConnection]] = {}
        self._sequences: dict[str, int] = {}

    async def connect(self, table_id: str, player_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        room = self._connections.setdefault(table_id, [])
        room.append(LiveConnection(player_id=player_id, websocket=websocket))

    def disconnect(self, table_id: str, websocket: WebSocket) -> str | None:
        room = self._connections.get(table_id, [])
        removed_player_id: str | None = None
        remaining: list[LiveConnection] = []
        for connection in room:
            if connection.websocket is websocket:
                removed_player_id = connection.player_id
                continue
            remaining.append(connection)

        if remaining:
            self._connections[table_id] = remaining
        elif table_id in self._connections:
            del self._connections[table_id]

        return removed_player_id

    async def send_snapshot(self, table_id: str, websocket: WebSocket, player_id: str) -> None:
        table = self.table_manager.tables.get(table_id)
        if table is None:
            sequence = self._next_sequence(table_id)
            await websocket.send_json(
                build_event(
                    event_type="error",
                    table_id=table_id,
                    sequence=sequence,
                    payload={"message": "Table not found"},
                ).model_dump()
            )
            return

        sequence = self._next_sequence(table_id)
        await websocket.send_json(
            build_event(
                event_type="table_snapshot",
                table_id=table_id,
                sequence=sequence,
                hand_id=table.active_hand.hand_id if table.active_hand is not None else None,
                payload=serialize_table_snapshot(table, player_id),
            ).model_dump()
        )

    async def broadcast_event(
        self,
        table_id: str,
        event_type: str,
        payload_factory,
        *,
        hand_id: int | None = None,
    ) -> None:
        room = self._connections.get(table_id, [])
        if not room:
            return

        sequence = self._next_sequence(table_id)
        for connection in list(room):
            payload = payload_factory(connection.player_id)
            await connection.websocket.send_json(
                build_event(
                    event_type=event_type,
                    table_id=table_id,
                    sequence=sequence,
                    hand_id=hand_id,
                    payload=payload,
                ).model_dump()
            )

    async def broadcast_snapshot(self, table_id: str) -> None:
        table = self.table_manager.tables.get(table_id)
        if table is None:
            return

        await self.broadcast_event(
            table_id,
            "table_state_updated",
            lambda viewer_id: serialize_table_snapshot(table, viewer_id),
            hand_id=table.active_hand.hand_id if table.active_hand is not None else None,
        )

    @staticmethod
    def _room_connections(room: list[LiveConnection]) -> list[LiveConnection]:
        return list(room)

    def _next_sequence(self, table_id: str) -> int:
        next_value = self._sequences.get(table_id, 0) + 1
        self._sequences[table_id] = next_value
        return next_value
