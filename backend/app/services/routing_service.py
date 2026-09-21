from app.schemas.routing import RouteStatusResponse
from app.services import graph_router


class RoutingService:

    def get_route_status(self, ambulance_id: str):
        # Real shortest-path routing on the road graph (see graph_router.py)
        return RouteStatusResponse(
            ambulance_id=ambulance_id,
            **graph_router.route_status(),
        )


routing_service = RoutingService()