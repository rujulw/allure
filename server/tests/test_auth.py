import pytest


@pytest.mark.asyncio
async def test_register_login_refresh_and_me(client):
    register_response = await client.post(
        "/auth/register",
        json={"email": "player@example.com", "password": "strong-pass-1"},
    )
    assert register_response.status_code == 201
    assert register_response.json()["email"] == "player@example.com"

    login_response = await client.post(
        "/auth/login",
        json={"email": "player@example.com", "password": "strong-pass-1"},
    )
    assert login_response.status_code == 200
    login_body = login_response.json()
    assert login_body["token_type"] == "bearer"
    assert login_body["access_token"]
    assert login_body["refresh_token"]

    me_response = await client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {login_body['access_token']}"},
    )
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "player@example.com"

    refresh_response = await client.post(
        "/auth/refresh",
        json={"refresh_token": login_body["refresh_token"]},
    )
    assert refresh_response.status_code == 200
    refresh_body = refresh_response.json()
    assert refresh_body["access_token"] != login_body["access_token"]
    assert refresh_body["refresh_token"] != login_body["refresh_token"]

    reused_refresh = await client.post(
        "/auth/refresh",
        json={"refresh_token": login_body["refresh_token"]},
    )
    assert reused_refresh.status_code == 401


@pytest.mark.asyncio
async def test_login_rejects_invalid_credentials(client):
    await client.post(
        "/auth/register",
        json={"email": "player2@example.com", "password": "strong-pass-1"},
    )

    response = await client.post(
        "/auth/login",
        json={"email": "player2@example.com", "password": "wrong-pass-1"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_protected_route_requires_token(client):
    response = await client.get("/auth/me")
    assert response.status_code == 401
