import pytest

from app.game.deck import Card
from app.game.evaluator import HandCategory, HandEvaluator


def cards(values: list[str]) -> list[Card]:
    return [Card.from_str(value) for value in values]


@pytest.mark.parametrize(
    ("hand_cards", "category"),
    [
        (["As", "Kd", "9c", "7h", "4d", "2s", "Jc"], HandCategory.HIGH_CARD),
        (["As", "Ad", "9c", "7h", "4d", "2s", "Jc"], HandCategory.ONE_PAIR),
        (["As", "Ad", "9c", "9h", "4d", "2s", "Jc"], HandCategory.TWO_PAIR),
        (["As", "Ad", "Ac", "7h", "4d", "2s", "Jc"], HandCategory.THREE_OF_A_KIND),
        (["9s", "8d", "7c", "6h", "5d", "2s", "Jc"], HandCategory.STRAIGHT),
        (["As", "Js", "9s", "7s", "4s", "2d", "Jc"], HandCategory.FLUSH),
        (["As", "Ad", "Ac", "7h", "7d", "2s", "Jc"], HandCategory.FULL_HOUSE),
        (["As", "Ad", "Ac", "Ah", "7d", "2s", "Jc"], HandCategory.FOUR_OF_A_KIND),
        (["9s", "8s", "7s", "6s", "5s", "2d", "Jc"], HandCategory.STRAIGHT_FLUSH),
        (["As", "Ks", "Qs", "Js", "Ts", "2d", "3c"], HandCategory.ROYAL_FLUSH),
    ],
)
def test_hand_evaluator_identifies_all_categories(hand_cards, category):
    result = HandEvaluator.evaluate(cards(hand_cards))
    assert result.category == category


def test_hand_evaluator_uses_best_five_cards_out_of_seven():
    result = HandEvaluator.evaluate(cards(["As", "Ah", "Ac", "Kd", "Kh", "2c", "3d"]))
    assert result.category == HandCategory.FULL_HOUSE
    assert result.tiebreaker == (14, 13)


def test_hand_evaluator_breaks_ties_with_kickers():
    better = cards(["As", "Ad", "Kc", "8h", "4d", "2s", "Jc"])
    worse = cards(["As", "Ad", "Qc", "8h", "4d", "2s", "Jc"])

    assert HandEvaluator.compare(better, worse) == 1
