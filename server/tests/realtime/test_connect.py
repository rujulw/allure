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


def test_websocket_connect_sends_snapshot(sync_client):
    create_table(sync_client.app.state.table_manager)
    token = auth_token(sync_client, "alice@example.com")

    with sync_client.websocket_connect(f"/ws/tables/alpha?token={token}") as websocket:
        message = websocket.receive_json()

    assert message["type"] == "table_snapshot"
    assert message["payload"]["table_id"] == "alpha"
    assert message["payload"]["phase"] == "open"


def test_join_command_broadcasts_player_joined(sync_client):
    create_table(sync_client.app.state.table_manager)
    token = auth_token(sync_client, "alice@example.com")

    with sync_client.websocket_connect(f"/ws/tables/alpha?token={token}") as websocket:
        websocket.receive_json()
        websocket.send_json({"type": "join_table", "payload": {}})
        event = websocket.receive_json()

    assert event["type"] == "player_joined"
    assert event["payload"]["player_id"] == "alice@example.com"
