from __future__ import annotations

from app.game.deck import Deck
from app.game.engine import GameEngine
from app.game.state import Action, Phase
from app.table.exceptions import (
    DuplicatePlayerError,
    HandStartError,
    InvalidBuyInError,
    InvalidSeatError,
    PlayerAlreadySeatedError,
    PlayerNotAtTableError,
    RejoinNotAvailableError,
    SeatOccupiedError,
    TableNotFoundError,
)
from app.table.state import BlindStructure, SeatState, TablePhase, TableState


class TableManager:
    def __init__(self):
        self.tables: dict[str, TableState] = {}
        self._engines: dict[str, GameEngine] = {}

    def create_table(
        self,
        *,
        table_id: str,
        max_seats: int,
        small_blind: int,
        big_blind: int,
        min_buy_in: int,
        max_buy_in: int,
    ) -> TableState:
        if max_seats < 2:
            raise ValueError("A table must support at least two seats")
        if min_buy_in <= 0 or max_buy_in <= 0 or min_buy_in > max_buy_in:
            raise ValueError("Buy-in range is invalid")
        if table_id in self.tables:
            raise ValueError(f"Table already exists: {table_id}")

        table = TableState(
            table_id=table_id,
            max_seats=max_seats,
            blind_structure=BlindStructure(small_blind=small_blind, big_blind=big_blind),
            min_buy_in=min_buy_in,
            max_buy_in=max_buy_in,
        )
        self.tables[table_id] = table
        self._refresh_phase(table)
        return table

    def join_table(self, table_id: str, player_id: str) -> TableState:
        table = self._table(table_id)
        seat = table.seat_for_player(player_id)
        if seat is not None:
            if seat.connected:
                raise DuplicatePlayerError(f"Player is already active at table: {player_id}")
            raise RejoinNotAvailableError(f"Player has a reserved seat and must rejoin: {player_id}")
        if player_id in table.waiting_player_ids:
            raise DuplicatePlayerError(f"Player is already waiting at table: {player_id}")

        table.waiting_player_ids.add(player_id)
        self._refresh_phase(table)
        return table

    def seat_player(self, table_id: str, player_id: str, seat_index: int, buy_in: int) -> TableState:
        table = self._table(table_id)
        self._validate_buy_in(table, buy_in)
        self._validate_seat_index(table, seat_index)

        if table.seats[seat_index] is not None:
            raise SeatOccupiedError(f"Seat {seat_index} is occupied")
        if table.seat_for_player(player_id) is not None:
            raise PlayerAlreadySeatedError(f"Player is already seated: {player_id}")
        if player_id not in table.waiting_player_ids:
            raise PlayerNotAtTableError(f"Player must join before taking a seat: {player_id}")

        table.waiting_player_ids.remove(player_id)
        table.seats[seat_index] = SeatState(seat_index=seat_index, player_id=player_id, stack=buy_in)
        self._refresh_phase(table)
        return table

    def leave_table(self, table_id: str, player_id: str) -> TableState:
        table = self._table(table_id)
        if player_id in table.waiting_player_ids:
            table.waiting_player_ids.remove(player_id)
            self._refresh_phase(table)
            return table

        seat = table.seat_for_player(player_id)
        if seat is None:
            raise PlayerNotAtTableError(f"Player is not seated at table: {player_id}")

        if table.phase == TablePhase.IN_HAND and table.active_hand is not None:
            seat.connected = False
            seat.sitting_out = True
            seat.pending_leave = True
        else:
            table.seats[seat.seat_index] = None

        self._refresh_phase(table)
        return table

    def rejoin_table(self, table_id: str, player_id: str) -> TableState:
        table = self._table(table_id)
        seat = table.seat_for_player(player_id)
        if seat is None or seat.connected:
            raise RejoinNotAvailableError(f"No disconnected seat is reserved for player: {player_id}")

        seat.connected = True
        seat.pending_leave = False
        self._refresh_phase(table)
        return table

    def sit_out(self, table_id: str, player_id: str, *, sitting_out: bool = True) -> TableState:
        table = self._table(table_id)
        seat = table.seat_for_player(player_id)
        if seat is None:
            raise PlayerNotAtTableError(f"Player is not seated at table: {player_id}")
        seat.sitting_out = sitting_out
        self._refresh_phase(table)
        return table

    def eligible_players_for_next_hand(self, table_id: str) -> list[SeatState]:
        table = self._table(table_id)
        return sorted(table.eligible_seats, key=lambda seat: seat.seat_index)

    def start_hand(self, table_id: str, deck: Deck | None = None) -> TableState:
        table = self._table(table_id)
        if table.phase == TablePhase.IN_HAND or table.active_hand is not None:
            raise HandStartError("Cannot start a new hand while another hand is active")

        eligible_seats = self.eligible_players_for_next_hand(table_id)
        if len(eligible_seats) < 2:
            raise HandStartError("Need at least two eligible seated players to start a hand")

        ordered_seats = sorted(eligible_seats, key=lambda seat: seat.seat_index)
        dealer_seat_index = self._next_button_seat(table, ordered_seats)
        dealer_local_index = next(
            index for index, seat in enumerate(ordered_seats) if seat.seat_index == dealer_seat_index
        )

        engine = GameEngine(
            [(seat.player_id, seat.stack) for seat in ordered_seats],
            dealer_index=dealer_local_index,
            small_blind=table.blind_structure.small_blind,
            big_blind=table.blind_structure.big_blind,
            deck=deck,
        )
        hand = engine.start_hand()

        table.hand_number += 1
        table.dealer_button_index = dealer_seat_index
        table.active_hand = hand
        table.active_seat_map = {seat.player_id: seat.seat_index for seat in ordered_seats}
        table.phase = TablePhase.IN_HAND
        self._engines[table_id] = engine
        return table

    def apply_action(self, table_id: str, action: Action) -> TableState:
        table = self._table(table_id)
        engine = self._engine(table_id)
        hand = engine.apply_action(action)
        table.active_hand = hand

        if hand.phase == Phase.COMPLETE:
            self._settle_completed_hand(table_id)
        return table

    def close_table(self, table_id: str) -> TableState:
        table = self._table(table_id)
        if table.phase == TablePhase.IN_HAND:
            raise HandStartError("Cannot close a table during an active hand")
        table.phase = TablePhase.CLOSED
        table.waiting_player_ids.clear()
        return table

    def _settle_completed_hand(self, table_id: str) -> None:
        table = self._table(table_id)
        engine = self._engine(table_id)
        hand = engine.state
        if hand is None:
            raise HandStartError("No completed hand is available to settle")

        for player in hand.players:
            seat_index = table.active_seat_map[player.player_id]
            seat = table.seats[seat_index]
            if seat is None:
                raise HandStartError(f"Seat disappeared during hand settlement: {seat_index}")
            seat.stack = player.stack

        for seat in list(table.seated_players):
            if seat.pending_leave:
                table.seats[seat.seat_index] = None
            elif seat.stack <= 0:
                seat.sitting_out = True

        table.active_hand = None
        table.active_seat_map.clear()
        self._engines.pop(table_id, None)
        self._refresh_phase(table)

    def _next_button_seat(self, table: TableState, ordered_seats: list[SeatState]) -> int:
        if table.dealer_button_index is None:
            return ordered_seats[0].seat_index

        for seat in ordered_seats:
            if seat.seat_index > table.dealer_button_index:
                return seat.seat_index
        return ordered_seats[0].seat_index

    def _refresh_phase(self, table: TableState) -> None:
        if table.phase == TablePhase.CLOSED:
            return
        if table.active_hand is not None:
            table.phase = TablePhase.IN_HAND
            return
        eligible_count = len(table.eligible_seats)
        if eligible_count >= 2:
            table.phase = TablePhase.READY
        elif table.seated_players or table.waiting_player_ids:
            table.phase = TablePhase.WAITING_FOR_PLAYERS
        else:
            table.phase = TablePhase.OPEN

    def _validate_buy_in(self, table: TableState, buy_in: int) -> None:
        if buy_in < table.min_buy_in or buy_in > table.max_buy_in:
            raise InvalidBuyInError(
                f"Buy-in must be between {table.min_buy_in} and {table.max_buy_in}: {buy_in}"
            )

    @staticmethod
    def _validate_seat_index(table: TableState, seat_index: int) -> None:
        if seat_index < 0 or seat_index >= table.max_seats:
            raise InvalidSeatError(f"Seat index is out of range: {seat_index}")

    def _table(self, table_id: str) -> TableState:
        table = self.tables.get(table_id)
        if table is None:
            raise TableNotFoundError(f"Table does not exist: {table_id}")
        return table

    def _engine(self, table_id: str) -> GameEngine:
        engine = self._engines.get(table_id)
        if engine is None:
            raise HandStartError(f"No active engine exists for table: {table_id}")
        return engine
