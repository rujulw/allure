from __future__ import annotations

from dataclasses import dataclass
from random import Random
from typing import ClassVar


@dataclass(frozen=True, order=True)
class Card:
    rank: int
    suit: str

    RANK_MAP: ClassVar[dict[str, int]] = {
        "2": 2,
        "3": 3,
        "4": 4,
        "5": 5,
        "6": 6,
        "7": 7,
        "8": 8,
        "9": 9,
        "T": 10,
        "J": 11,
        "Q": 12,
        "K": 13,
        "A": 14,
    }
    RANK_NAMES: ClassVar[dict[int, str]] = {value: key for key, value in RANK_MAP.items()}
    SUITS: ClassVar[tuple[str, ...]] = ("s", "h", "d", "c")

    def __post_init__(self) -> None:
        if self.rank not in self.RANK_NAMES:
            raise ValueError(f"Unsupported rank: {self.rank}")
        if self.suit not in self.SUITS:
            raise ValueError(f"Unsupported suit: {self.suit}")

    @classmethod
    def from_str(cls, value: str) -> "Card":
        if len(value) != 2:
            raise ValueError(f"Card notation must be two characters: {value}")
        rank_token, suit = value[0].upper(), value[1].lower()
        rank = cls.RANK_MAP.get(rank_token)
        if rank is None:
            raise ValueError(f"Unsupported card rank: {value}")
        return cls(rank=rank, suit=suit)

    def __str__(self) -> str:
        return f"{self.RANK_NAMES[self.rank]}{self.suit}"


class Deck:
    def __init__(self, cards: list[Card] | None = None):
        self.cards = list(cards) if cards is not None else self._standard_deck()

    @staticmethod
    def _standard_deck() -> list[Card]:
        return [Card(rank=rank, suit=suit) for suit in Card.SUITS for rank in range(2, 15)]

    def shuffle(self, rng: Random | None = None) -> None:
        randomizer = rng or Random()
        randomizer.shuffle(self.cards)

    def deal(self, count: int = 1) -> list[Card]:
        if count < 1:
            raise ValueError("Deal count must be positive")
        if count > len(self.cards):
            raise ValueError("Not enough cards left in deck")

        dealt = self.cards[:count]
        del self.cards[:count]
        return dealt
