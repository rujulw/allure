from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from app.game.deck import Card


class Street(str, Enum):
    PREFLOP = "preflop"
    FLOP = "flop"
    TURN = "turn"
    RIVER = "river"
    SHOWDOWN = "showdown"


class Phase(str, Enum):
    BETTING = "betting"
    SHOWDOWN = "showdown"
    COMPLETE = "complete"


class ActionType(str, Enum):
    FOLD = "fold"
    CHECK = "check"
    CALL = "call"
    RAISE = "raise"
    ALL_IN = "all_in"


@dataclass(frozen=True)
class Action:
    player_id: str
    action_type: ActionType
    amount: int | None = None


@dataclass(frozen=True)
class LegalAction:
    action_type: ActionType
    amount: int | None = None
    min_amount: int | None = None
    max_amount: int | None = None
    call_amount: int = 0


@dataclass(frozen=True)
class Pot:
    amount: int
    eligible_player_ids: tuple[str, ...]


@dataclass
class PlayerState:
    player_id: str
    seat_index: int
    stack: int
    hole_cards: list[Card] = field(default_factory=list)
    folded: bool = False
    all_in: bool = False
    has_acted: bool = False
    current_bet: int = 0
    total_committed: int = 0
    winnings: int = 0
    is_dealer: bool = False
    is_small_blind: bool = False
    is_big_blind: bool = False
    last_action: ActionType | None = None

    @property
    def in_hand(self) -> bool:
        return not self.folded and (self.stack > 0 or self.total_committed > 0)

    @property
    def can_act(self) -> bool:
        return not self.folded and not self.all_in and self.stack > 0


@dataclass
class HandState:
    hand_id: int
    phase: Phase
    street: Street
    dealer_index: int
    small_blind: int
    big_blind: int
    players: list[PlayerState]
    deck: list[Card]
    community_cards: list[Card] = field(default_factory=list)
    pot: int = 0
    pots: list[Pot] = field(default_factory=list)
    current_actor_index: int | None = None
    current_bet: int = 0
    last_full_raise: int = 0
    legal_actions: list[LegalAction] = field(default_factory=list)
    action_history: list[Action] = field(default_factory=list)
    winner_ids: list[str] = field(default_factory=list)
    payouts: dict[str, int] = field(default_factory=dict)

    @property
    def current_actor(self) -> PlayerState | None:
        if self.current_actor_index is None:
            return None
        return self.players[self.current_actor_index]
