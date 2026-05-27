from __future__ import annotations

from collections.abc import Sequence

from app.game.state import PlayerState, Pot


class PotCalculator:
    @staticmethod
    def build_pots(players: Sequence[PlayerState]) -> list[Pot]:
        levels = sorted({player.total_committed for player in players if player.total_committed > 0})
        if not levels:
            return []

        pots: list[Pot] = []
        previous_level = 0
        for level in levels:
            contributors = [player for player in players if player.total_committed >= level]
            amount = (level - previous_level) * len(contributors)
            eligible = tuple(
                player.player_id
                for player in sorted(contributors, key=lambda value: value.seat_index)
                if not player.folded
            )
            pots.append(Pot(amount=amount, eligible_player_ids=eligible))
            previous_level = level

        return pots
