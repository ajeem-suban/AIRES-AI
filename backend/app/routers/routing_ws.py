import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.live import hub
from app.services.routing_service import routing_service
router = APIRouter()


@router.websocket("/ws/routing/{ambulance_id}")
async def routing_socket(
    websocket: WebSocket,
    ambulance_id: str,
):

    await websocket.accept()
    changed = hub.subscribe()

    try:
        while True:
            route = routing_service.get_route_status(ambulance_id)
            await websocket.send_json(route.model_dump())

            # Wake up instantly when an event is injected or cleared;
            # otherwise refresh every 5 seconds as before.
            try:
                await asyncio.wait_for(changed.wait(), timeout=5)
            except asyncio.TimeoutError:
                pass
            changed.clear()
    except WebSocketDisconnect:
        pass
    finally:
        hub.unsubscribe(changed)  # no leftover listeners after a client leaves