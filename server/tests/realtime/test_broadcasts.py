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


def test_hole_cards_stay_private_in_snapshots(sync_client):
    create_table(sync_client.app.state.table_manager)
    alice = auth_token(sync_client, "alice@example.com")
    bob = auth_token(sync_client, "bob@example.com")

    with sync_client.websocket_connect(f"/ws/tables/alpha?token={alice}") as ws_alice:
        with sync_client.websocket_connect(f"/ws/tables/alpha?token={bob}") as ws_bob:
            ws_alice.receive_json()
            ws_bob.receive_json()
            ws_alice.send_json({"type": "join_table", "payload": {}})
            ws_bob.send_json({"type": "join_table", "payload": {}})
            ws_alice.receive_json()
            ws_bob.receive_json()
            ws_alice.receive_json()
            ws_bob.receive_json()
            ws_alice.send_json({"type": "take_seat", "payload": {"seat_index": 0, "buy_in": 1000}})
            ws_alice.receive_json()
            ws_bob.receive_json()
            ws_bob.send_json({"type": "take_seat", "payload": {"seat_index": 1, "buy_in": 1000}})
            ws_alice.receive_json()
            ws_bob.receive_json()
            ws_alice.send_json({"type": "start_hand", "payload": {}})
            ws_alice.receive_json()
            alice_cards = ws_alice.receive_json()
            ws_alice.receive_json()
            ws_bob.receive_json()
            bob_cards = ws_bob.receive_json()
            ws_bob.receive_json()

    alice_visible = alice_cards["payload"]["hand"]["visible_hole_cards"]
    bob_visible = bob_cards["payload"]["hand"]["visible_hole_cards"]
    assert "alice@example.com" in alice_visible
    assert "bob@example.com" not in alice_visible
    assert "bob@example.com" in bob_visible
    assert "alice@example.com" not in bob_visible
