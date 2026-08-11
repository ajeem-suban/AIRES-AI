from fastapi import APIRouter

from app.schemas.routing import RouteStatusResponse
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