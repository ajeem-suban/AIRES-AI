from app.schemas.routing import RouteStatusResponse
from app.services.road_ai_service import road_ai_service


class RoutingService:

    def get_route_status(self, ambulance_id: str):

        # Simulate AI road event detection
        event = road_ai_service.detect_event()

        current_route = "Main Road"
        old_eta = 8

        # AI Decision Engine
        if event["event_type"] == "Clear":

            traffic = "Light"
            recommended_route = "Main Road"
            new_eta = 8
            rerouted = False

        elif event["event_type"] == "Traffic Jam":

            traffic = "Moderate"
            recommended_route = "Bypass Road"
            new_eta = 6
            rerouted = True

        elif event["event_type"] == "Construction":

            traffic = "Heavy"
            recommended_route = "Ring Road"
            new_eta = 5
            rerouted = True

        elif event["event_type"] == "Accident":

            traffic = "Heavy"
            recommended_route = "Emergency Route"
            new_eta = 4
            rerouted = True

        elif event["event_type"] == "Flood":

            traffic = "Heavy"
            recommended_route = "Highway Diversion"
            new_eta = 7
            rerouted = True

        else:

            traffic = "Moderate"
            recommended_route = current_route
            new_eta = old_eta
            rerouted = False

        return RouteStatusResponse(
    ambulance_id=ambulance_id,

    current_route=current_route,
    recommended_route=recommended_route,

    traffic_status=traffic,

    road_event=event["event_type"],
    event_description=event["description"],

    rerouted=rerouted,

    old_eta=old_eta,
    new_eta=new_eta,

    time_saved=old_eta - new_eta,
)


routing_service = RoutingService()