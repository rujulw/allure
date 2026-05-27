from app.game.pot import PotCalculator
from app.game.state import PlayerState


def player(player_id: str, seat_index: int, committed: int, folded: bool = False) -> PlayerState:
    state = PlayerState(player_id=player_id, seat_index=seat_index, stack=0)
    state.total_committed = committed
    state.folded = folded
    state.all_in = committed > 0
    return state


def test_pot_calculator_builds_main_and_side_pots():
    players = [
        player("alice", 0, 100),
        player("bob", 1, 300),
        player("carol", 2, 300),
    ]

    pots = PotCalculator.build_pots(players)

    assert [(pot.amount, pot.eligible_player_ids) for pot in pots] == [
        (300, ("alice", "bob", "carol")),
        (400, ("bob", "carol")),
    ]


def test_folded_player_contributes_but_is_not_eligible():
    players = [
        player("alice", 0, 100, folded=True),
        player("bob", 1, 100),
        player("carol", 2, 200),
    ]

    pots = PotCalculator.build_pots(players)

    assert [(pot.amount, pot.eligible_player_ids) for pot in pots] == [
        (300, ("bob", "carol")),
        (100, ("carol",)),
    ]
