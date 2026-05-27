from app.table.manager import TableManager
from app.table.state import TablePhase


def test_leave_before_hand_starts_immediately_frees_seat():
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
    manager.seat_player("alpha", "alice", seat_index=2, buy_in=1_500)

    manager.leave_table("alpha", "alice")

    assert table.seats[2] is None
    assert table.phase == TablePhase.OPEN


def test_rejoin_restores_same_seat_during_active_hand():
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
    manager.start_hand("alpha")

    manager.leave_table("alpha", "alice")
    seat = table.seats[0]

    assert seat is not None
    assert seat.connected is False
    assert seat.pending_leave is True

    manager.rejoin_table("alpha", "alice")

    assert table.seats[0] is seat
    assert seat.connected is True
    assert seat.pending_leave is False
