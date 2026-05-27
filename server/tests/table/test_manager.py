from app.game.deck import Card, Deck
from app.game.state import Action, ActionType
from app.table.exceptions import HandStartError, SeatOccupiedError
from app.table.manager import TableManager
from app.table.state import TablePhase


def cards(values: list[str]) -> list[Card]:
    return [Card.from_str(value) for value in values]


def test_seat_assignment_rejects_occupied_seat():
    manager = TableManager()
    manager.create_table(
        table_id="alpha",
        max_seats=6,
        small_blind=50,
        big_blind=100,
        min_buy_in=1_000,
        max_buy_in=5_000,
    )
    manager.join_table("alpha", "alice")
    manager.join_table("alpha", "bob")
    manager.seat_player("alpha", "alice", seat_index=1, buy_in=1_000)

    try:
        manager.seat_player("alpha", "bob", seat_index=1, buy_in=1_500)
    except SeatOccupiedError:
        pass
    else:
        raise AssertionError("Expected SeatOccupiedError")


def test_cannot_start_hand_without_two_eligible_players():
    manager = TableManager()
    manager.create_table(
        table_id="alpha",
        max_seats=6,
        small_blind=50,
        big_blind=100,
        min_buy_in=1_000,
        max_buy_in=5_000,
    )
    manager.join_table("alpha", "alice")
    manager.seat_player("alpha", "alice", seat_index=0, buy_in=1_000)

    try:
        manager.start_hand("alpha")
    except HandStartError:
        pass
    else:
        raise AssertionError("Expected HandStartError")


def test_start_hand_and_settlement_sync_table_stacks():
    manager = TableManager()
    table = manager.create_table(
        table_id="alpha",
        max_seats=6,
        small_blind=50,
        big_blind=100,
        min_buy_in=1_000,
        max_buy_in=5_000,
    )
    manager.join_table("alpha", "alice")
    manager.join_table("alpha", "bob")
    manager.seat_player("alpha", "alice", seat_index=2, buy_in=1_000)
    manager.seat_player("alpha", "bob", seat_index=4, buy_in=1_000)

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
    manager.start_hand("alpha", deck=deck)
    assert table.phase == TablePhase.IN_HAND
    assert table.active_hand is not None

    manager.apply_action("alpha", Action("alice", ActionType.CALL))
    manager.apply_action("alpha", Action("bob", ActionType.CHECK))
    manager.apply_action("alpha", Action("bob", ActionType.CHECK))
    manager.apply_action("alpha", Action("alice", ActionType.CHECK))
    manager.apply_action("alpha", Action("bob", ActionType.CHECK))
    manager.apply_action("alpha", Action("alice", ActionType.CHECK))
    manager.apply_action("alpha", Action("bob", ActionType.CHECK))
    manager.apply_action("alpha", Action("alice", ActionType.CHECK))

    assert table.phase == TablePhase.READY
    assert table.active_hand is None
    assert table.seats[2] is not None
    assert table.seats[2].stack == 1_100
    assert table.seats[4] is not None
    assert table.seats[4].stack == 900


def test_pending_leave_is_cleaned_up_after_hand_settlement():
    manager = TableManager()
    table = manager.create_table(
        table_id="alpha",
        max_seats=6,
        small_blind=50,
        big_blind=100,
        min_buy_in=1_000,
        max_buy_in=5_000,
    )
    manager.join_table("alpha", "alice")
    manager.join_table("alpha", "bob")
    manager.seat_player("alpha", "alice", seat_index=0, buy_in=1_000)
    manager.seat_player("alpha", "bob", seat_index=1, buy_in=1_000)

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
    manager.start_hand("alpha", deck=deck)
    manager.leave_table("alpha", "alice")

    manager.apply_action("alpha", Action("alice", ActionType.CALL))
    manager.apply_action("alpha", Action("bob", ActionType.CHECK))
    manager.apply_action("alpha", Action("bob", ActionType.CHECK))
    manager.apply_action("alpha", Action("alice", ActionType.CHECK))
    manager.apply_action("alpha", Action("bob", ActionType.CHECK))
    manager.apply_action("alpha", Action("alice", ActionType.CHECK))
    manager.apply_action("alpha", Action("bob", ActionType.CHECK))
    manager.apply_action("alpha", Action("alice", ActionType.CHECK))

    assert table.seats[0] is None
    assert table.seats[1] is not None
