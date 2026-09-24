from pydantic import BaseModel, Field


class RoadEvent(BaseModel):
    """One road event, placed at the middle of its road for the map marker."""
    type: str
    road: str
    lat: float
    lon: float


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
    clear_eta: int = 0  # ETA with no events on the route; the dashboards use it for the delay
    hospital: str = ""  # hospital name of the chosen trip ("" = use the dashboard default)
    distance_km: float = 0
    clear_km: float = 0
    ambulance: list[float] = Field(default_factory=list)  # [lat, lon] right now
    arrived: bool = False
    step_seconds: float = 3
    move_path: list[list[float]] = Field(default_factory=list)  # road shape of the last move # ETA with no events on the route; the dashboards use it for the delay

    # Map data: lists of [lat, lon] points, plus one marker per active event.
    # Defaults keep things working even if a field is missing.
    current_path: list[list[float]] = Field(default_factory=list)
    recommended_path: list[list[float]] = Field(default_factory=list)
    events: list[RoadEvent] = Field(default_factory=list)