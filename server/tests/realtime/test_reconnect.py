from app.table.manager import TableManager


def create_table(manager: TableManager) -> None:
    manager.create_table(
        table_id="alpha",
        max_seats=6,
        small_blind=50,
        big_blind=100,
        min_buy_in=1_000,
        max_buy_in=5_000,
    )


def auth_token(sync_client, email: str) -> str:
    sync_client.post("/auth/register", json={"email": email, "password": "strong-pass-1"})
    response = sync_client.post("/auth/login", json={"email": email, "password": "strong-pass-1"})
    return response.json()["access_token"]


def test_reconnect_snapshot_recovers_reserved_seat(sync_client):
    create_table(sync_client.app.state.table_manager)
    token = auth_token(sync_client, "alice@example.com")

    with sync_client.websocket_connect(f"/ws/tables/alpha?token={token}") as websocket:
        websocket.receive_json()
        websocket.send_json({"type": "join_table", "payload": {}})
        websocket.receive_json()
        websocket.send_json({"type": "take_seat", "payload": {"seat_index": 2, "buy_in": 1000}})
        websocket.receive_json()

    table = sync_client.app.state.table_manager.tables["alpha"]
    assert table.seats[2] is not None
    assert table.seats[2].connected is False

    with sync_client.websocket_connect(f"/ws/tables/alpha?token={token}") as websocket:
        snapshot = websocket.receive_json()
        websocket.send_json({"type": "rejoin_table", "payload": {}})
        rejoin_event = websocket.receive_json()

    assert snapshot["type"] == "table_snapshot"
    assert snapshot["payload"]["seats"][2]["connected"] is False
    assert rejoin_event["type"] == "player_rejoined"
