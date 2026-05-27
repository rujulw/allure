import pytest

from app.table.exceptions import InvalidBuyInError
from app.table.manager import TableManager


def test_buy_in_must_stay_within_table_range():
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

    with pytest.raises(InvalidBuyInError):
        manager.seat_player("alpha", "alice", seat_index=0, buy_in=500)


def test_valid_buy_in_seats_player_and_makes_table_ready():
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
    manager.seat_player("alpha", "alice", seat_index=0, buy_in=1_500)
    manager.seat_player("alpha", "bob", seat_index=3, buy_in=2_000)

    assert table.seats[0] is not None
    assert table.seats[0].stack == 1_500
    assert table.phase.value == "ready"
