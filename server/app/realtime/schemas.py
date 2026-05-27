from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class EventEnvelope(BaseModel):
    type: str
    table_id: str
    sequence: int
    hand_id: int | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class CommandEnvelope(BaseModel):
    type: Literal[
        "join_table",
        "take_seat",
        "leave_table",
        "rejoin_table",
        "sit_out",
        "start_hand",
        "player_action",
        "request_snapshot",
    ]
    payload: dict[str, Any] = Field(default_factory=dict)
