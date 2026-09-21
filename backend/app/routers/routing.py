from fastapi import APIRouter, HTTPException

from app.schemas.routing import RouteStatusResponse
from app.services import graph_router
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

@router.post("/event")
def inject_road_event(event_type: str, road_name: str | None = None):
    """Demo control panel: e.g. POST /routing/event?event_type=Accident"""
    try:
        return graph_router.inject_event(event_type, road_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/events")
def clear_road_events():
    return graph_router.clear_events()