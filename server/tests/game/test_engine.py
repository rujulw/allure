from app.game.deck import Card, Deck
from app.game.engine import GameEngine
from app.game.state import Action, ActionType, Phase, Street


def cards(values: list[str]) -> list[Card]:
    return [Card.from_str(value) for value in values]


def test_start_hand_posts_blinds_and_sets_preflop_actor():
    deck = Deck(cards=cards(["As", "Kd", "Qc", "Jh", "Ts", "9d", "8c", "7h", "6s"]))
    engine = GameEngine(
        [("alice", 1_000), ("bob", 1_000), ("carol", 1_000)],
        dealer_index=0,
        small_blind=50,
        big_blind=100,
        deck=deck,
    )

    state = engine.start_hand()

    assert state.street == Street.PREFLOP
    assert state.players[1].is_small_blind
    assert state.players[2].is_big_blind
    assert state.current_actor.player_id == "alice"
    assert {action.action_type for action in state.legal_actions} == {
        ActionType.FOLD,
        ActionType.CALL,
        ActionType.RAISE,
        ActionType.ALL_IN,
    }


def test_heads_up_hand_advances_to_showdown_and_awards_pot():
    deck = Deck(
        cards=cards(
            [
                "Kc",
                "As",
                "Kd",
                "Ah",
                "2c",
                "7d",
                "9h",
                "Jc",
                "3s",
            ]
        )
    )
    engine = GameEngine(
        [("alice", 1_000), ("bob", 1_000)],
        dealer_index=0,
        small_blind=50,
        big_blind=100,
        deck=deck,
    )

    state = engine.start_hand()
    assert state.current_actor.player_id == "alice"

    engine.apply_action(Action("alice", ActionType.CALL))
    assert state.street == Street.PREFLOP
    assert state.current_actor.player_id == "bob"

    engine.apply_action(Action("bob", ActionType.CHECK))
    assert state.street == Street.FLOP
    assert [str(card) for card in state.community_cards] == ["2c", "7d", "9h"]
    assert state.current_actor.player_id == "bob"

    engine.apply_action(Action("bob", ActionType.CHECK))
    engine.apply_action(Action("alice", ActionType.CHECK))
    assert state.street == Street.TURN

    engine.apply_action(Action("bob", ActionType.CHECK))
    engine.apply_action(Action("alice", ActionType.CHECK))
    assert state.street == Street.RIVER

    engine.apply_action(Action("bob", ActionType.CHECK))
    engine.apply_action(Action("alice", ActionType.CHECK))

    assert state.phase == Phase.COMPLETE
    assert state.street == Street.SHOWDOWN
    assert state.winner_ids == ["alice"]
    assert state.players[0].stack == 1_100
    assert state.players[1].stack == 900


def test_all_in_call_fast_forwards_to_showdown():
    deck = Deck(
        cards=cards(
            [
                "Kc",
                "As",
                "Kd",
                "Ah",
                "2c",
                "7d",
                "9h",
                "Jc",
                "3s",
            ]
        )
    )
    engine = GameEngine(
        [("alice", 150), ("bob", 1_000)],
        dealer_index=0,
        small_blind=50,
        big_blind=100,
        deck=deck,
    )

    state = engine.start_hand()
    engine.apply_action(Action("alice", ActionType.ALL_IN))
    engine.apply_action(Action("bob", ActionType.CALL))

    assert state.phase == Phase.COMPLETE
    assert len(state.community_cards) == 5
    assert state.winner_ids == ["alice"]
    assert state.players[0].stack == 300
    assert state.players[1].stack == 850
