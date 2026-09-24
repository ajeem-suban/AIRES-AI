import asyncio

from fastapi import APIRouter, HTTPException

from app.schemas.routing import RouteStatusResponse
from app.services import real_router as graph_router
from app.services.live import hub
from app.services.routing_service import routing_service

router = APIRouter(
    prefix="/routing",
    tags=["Dynamic Routing"],
)


@router.get(
    "/status/{ambulance_id}",
    response_model=RouteStatusResponse,
)
def get_route_status(ambulance_id: str):

    return routing_service.get_route_status(ambulance_id)

# These are async on purpose: hub.notify() must run on the event loop,
# and the route math is small enough that it will not block anything.
@router.post("/event")
async def inject_road_event(event_type: str, road_name: str | None = None, position: str = "random"):
    """Demo control panel: e.g. POST /routing/event?event_type=Accident"""
    try:
        result = graph_router.inject_event(event_type, road_name, position)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    hub.notify()  # push the new route to every open map right now
    return result


_trip_task = None   # the background "driving" task


def _stop():
    """Cancel the driving task if it is running."""
    global _trip_task
    if _trip_task and not _trip_task.done():
        _trip_task.cancel()
    _trip_task = None


async def _drive():
    """Every few seconds, move the ambulance one junction and tell all screens."""
    while True:
        await asyncio.sleep(graph_router.STEP_SECONDS)
        more = graph_router.advance()
        hub.notify()
        if not more:
            break


@router.post("/start")
async def start_trip():
    global _trip_task
    if _trip_task and not _trip_task.done():
        return {"message": "Already driving."}
    if graph_router.arrived():
        graph_router.reset_position()
    _trip_task = asyncio.create_task(_drive())
    hub.notify()
    return {"message": "Ambulance dispatched."}


@router.post("/reset")
async def reset_trip():
    _stop()
    result = graph_router.reset_position()
    hub.notify()
    return result


@router.post("/trip")
async def choose_trip(name: str):
    """Demo control panel: Auto, Short, Medium or Long trip."""
    try:
        _stop()
        result = graph_router.set_trip(name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    hub.notify()
    return result


@router.delete("/events")
async def clear_road_events():
    result = graph_router.clear_events()
    hub.notify()
    return results