from pydantic import BaseModel


class RouteStatusResponse(BaseModel):
    ambulance_id: str

    current_route: str
    recommended_route: str

    traffic_status: str

    road_event: str
    event_description: str

    rerouted: bool

    old_eta: int
    new_eta: int

    time_saved: int