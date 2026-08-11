import asyncio

from fastapi import APIRouter, WebSocket

from app.services.routing_service import routing_service

router = APIRouter()


@router.websocket("/ws/routing/{ambulance_id}")
async def routing_socket(
    websocket: WebSocket,
    ambulance_id: str,
):

    await websocket.accept()

    while True:

        route = routing_service.get_route_status(ambulance_id)

        await websocket.send_json(route.model_dump())

        await asyncio.sleep(5)