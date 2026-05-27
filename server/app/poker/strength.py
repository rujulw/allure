from __future__ import annotations

from collections.abc import Sequence

from app.game.deck import Card


def score_hand_strength(hole_cards: Sequence[Card], community_cards: Sequence[Card]) -> float:
    """Return a fast heuristic strength score for future bot decision-making.

    This interface is reserved for the bot curriculum and should stay unimplemented
    in the game-engine milestone.
    """

    raise NotImplementedError("Hand strength heuristics are implemented in later bot milestones")
