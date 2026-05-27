from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from app.auth import get_access_subject
from app.realtime.session import handle_socket_session

router = APIRouter(tags=["realtime"])


@router.websocket("/ws/tables/{table_id}")
async def table_socket(websocket: WebSocket, table_id: str) -> None:
    token = websocket.query_params.get("token")
    if token is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    try:
        player_id = get_access_subject(token)
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    realtime_manager = websocket.app.state.realtime_manager
    await realtime_manager.connect(table_id, player_id, websocket)

    try:
        await handle_socket_session(
            websocket,
            table_id=table_id,
            player_id=player_id,
            realtime_manager=realtime_manager,
        )
    except WebSocketDisconnect:
        realtime_manager.disconnect(table_id, websocket)
