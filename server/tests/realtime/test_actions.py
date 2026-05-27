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


def test_start_hand_and_action_flow_broadcasts_events(sync_client):
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
            seat_event = ws_alice.receive_json()
            ws_bob.receive_json()
            assert seat_event["type"] == "player_seated"

            ws_bob.send_json({"type": "take_seat", "payload": {"seat_index": 1, "buy_in": 1000}})
            ws_alice.receive_json()
            ws_bob.receive_json()

            ws_alice.send_json({"type": "start_hand", "payload": {}})
            hand_started = ws_alice.receive_json()
            cards_dealt = ws_alice.receive_json()
            action_requested = ws_alice.receive_json()

            assert hand_started["type"] == "hand_started"
            assert cards_dealt["type"] == "cards_dealt"
            assert action_requested["type"] == "action_requested"

            ws_alice.send_json({"type": "player_action", "payload": {"action_type": "call"}})
            applied = ws_alice.receive_json()
            pot_updated = ws_alice.receive_json()
            next_action = ws_alice.receive_json()

            assert applied["type"] == "action_applied"
            assert applied["payload"]["action_type"] == "call"
            assert pot_updated["type"] == "pot_updated"
            assert next_action["type"] == "action_requested"
