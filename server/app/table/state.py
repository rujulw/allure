from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from app.game.state import HandState


class TablePhase(str, Enum):
    OPEN = "open"
    WAITING_FOR_PLAYERS = "waiting_for_players"
    READY = "ready"
    IN_HAND = "in_hand"
    CLOSED = "closed"


@dataclass(frozen=True)
class BlindStructure:
    small_blind: int
    big_blind: int

    def __post_init__(self) -> None:
        if self.small_blind <= 0 or self.big_blind <= 0:
            raise ValueError("Blinds must be positive")
        if self.small_blind > self.big_blind:
            raise ValueError("Small blind cannot exceed big blind")


@dataclass
class SeatState:
    seat_index: int
    player_id: str
    stack: int
    connected: bool = True
    sitting_out: bool = False
    pending_leave: bool = False

    @property
    def eligible_for_next_hand(self) -> bool:
        return self.connected and not self.sitting_out and not self.pending_leave and self.stack > 0


@dataclass
class TableState:
    table_id: str
    max_seats: int
    blind_structure: BlindStructure
    min_buy_in: int
    max_buy_in: int
    phase: TablePhase = TablePhase.OPEN
    seats: list[SeatState | None] = field(default_factory=list)
    waiting_player_ids: set[str] = field(default_factory=set)
    dealer_button_index: int | None = None
    active_hand: HandState | None = None
    active_seat_map: dict[str, int] = field(default_factory=dict)
    hand_number: int = 0

    def __post_init__(self) -> None:
        if not self.seats:
            self.seats = [None for _ in range(self.max_seats)]

    @property
    def seated_players(self) -> list[SeatState]:
        return [seat for seat in self.seats if seat is not None]

    @property
    def eligible_seats(self) -> list[SeatState]:
        return [seat for seat in self.seated_players if seat.eligible_for_next_hand]

    def seat_for_player(self, player_id: str) -> SeatState | None:
        for seat in self.seated_players:
            if seat.player_id == player_id:
                return seat
        return None
