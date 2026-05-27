from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from enum import IntEnum
from itertools import combinations
from typing import Iterable, Sequence

from app.game.deck import Card


class HandCategory(IntEnum):
    HIGH_CARD = 1
    ONE_PAIR = 2
    TWO_PAIR = 3
    THREE_OF_A_KIND = 4
    STRAIGHT = 5
    FLUSH = 6
    FULL_HOUSE = 7
    FOUR_OF_A_KIND = 8
    STRAIGHT_FLUSH = 9
    ROYAL_FLUSH = 10


@dataclass(frozen=True)
class EvaluatedHand:
    category: HandCategory
    tiebreaker: tuple[int, ...]
    cards: tuple[Card, ...]

    @property
    def comparison_key(self) -> tuple[int, tuple[int, ...]]:
        return (int(self.category), self.tiebreaker)


class HandEvaluator:
    @classmethod
    def evaluate(cls, cards: Sequence[Card]) -> EvaluatedHand:
        if len(cards) < 5 or len(cards) > 7:
            raise ValueError("Hand evaluation expects between 5 and 7 cards")

        best_hand: EvaluatedHand | None = None
        for five_cards in combinations(cards, 5):
            candidate = cls._evaluate_five_cards(five_cards)
            if best_hand is None or candidate.comparison_key > best_hand.comparison_key:
                best_hand = candidate

        if best_hand is None:
            raise ValueError("Unable to evaluate hand")
        return best_hand

    @classmethod
    def compare(cls, first: Sequence[Card], second: Sequence[Card]) -> int:
        first_hand = cls.evaluate(first)
        second_hand = cls.evaluate(second)
        if first_hand.comparison_key > second_hand.comparison_key:
            return 1
        if first_hand.comparison_key < second_hand.comparison_key:
            return -1
        return 0

    @classmethod
    def _evaluate_five_cards(cls, cards: Iterable[Card]) -> EvaluatedHand:
        five_cards = tuple(sorted(cards, key=lambda card: card.rank, reverse=True))
        ranks = [card.rank for card in five_cards]
        suits = {card.suit for card in five_cards}
        counts = Counter(ranks)
        ordered_counts = sorted(counts.items(), key=lambda item: (-item[1], -item[0]))

        is_flush = len(suits) == 1
        straight_high = cls._straight_high_card(ranks)

        if is_flush and straight_high:
            if straight_high == 14 and set(ranks) == {10, 11, 12, 13, 14}:
                return EvaluatedHand(HandCategory.ROYAL_FLUSH, (14,), five_cards)
            return EvaluatedHand(HandCategory.STRAIGHT_FLUSH, (straight_high,), five_cards)

        if ordered_counts[0][1] == 4:
            four_rank = ordered_counts[0][0]
            kicker = max(rank for rank in ranks if rank != four_rank)
            return EvaluatedHand(HandCategory.FOUR_OF_A_KIND, (four_rank, kicker), five_cards)

        if ordered_counts[0][1] == 3 and ordered_counts[1][1] == 2:
            return EvaluatedHand(
                HandCategory.FULL_HOUSE,
                (ordered_counts[0][0], ordered_counts[1][0]),
                five_cards,
            )

        if is_flush:
            return EvaluatedHand(HandCategory.FLUSH, tuple(sorted(ranks, reverse=True)), five_cards)

        if straight_high:
            return EvaluatedHand(HandCategory.STRAIGHT, (straight_high,), five_cards)

        if ordered_counts[0][1] == 3:
            trips = ordered_counts[0][0]
            kickers = tuple(rank for rank in sorted(ranks, reverse=True) if rank != trips)
            return EvaluatedHand(HandCategory.THREE_OF_A_KIND, (trips,) + kickers, five_cards)

        if ordered_counts[0][1] == 2 and ordered_counts[1][1] == 2:
            pair_ranks = sorted((ordered_counts[0][0], ordered_counts[1][0]), reverse=True)
            kicker = max(rank for rank in ranks if rank not in pair_ranks)
            return EvaluatedHand(HandCategory.TWO_PAIR, tuple(pair_ranks) + (kicker,), five_cards)

        if ordered_counts[0][1] == 2:
            pair_rank = ordered_counts[0][0]
            kickers = tuple(rank for rank in sorted(ranks, reverse=True) if rank != pair_rank)
            return EvaluatedHand(HandCategory.ONE_PAIR, (pair_rank,) + kickers, five_cards)

        return EvaluatedHand(HandCategory.HIGH_CARD, tuple(sorted(ranks, reverse=True)), five_cards)

    @staticmethod
    def _straight_high_card(ranks: Sequence[int]) -> int | None:
        unique_ranks = sorted(set(ranks), reverse=True)
        if len(unique_ranks) != 5:
            return None

        if unique_ranks == [14, 5, 4, 3, 2]:
            return 5

        if unique_ranks[0] - unique_ranks[-1] == 4:
            return unique_ranks[0]

        return None
