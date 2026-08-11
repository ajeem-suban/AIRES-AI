from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.tracking_service import AmbulanceTracker

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/tracking")
async def websocket_tracking(websocket: WebSocket):

    await websocket.accept()

    try:
        tracker = AmbulanceTracker()

        async for location in tracker.track():
            await websocket.send_json(location)

    except ValueError as e:
        await websocket.send_json({"error": str(e)})
        await websocket.close()

    except WebSocketDisconnect:
        print("Client disconnected")