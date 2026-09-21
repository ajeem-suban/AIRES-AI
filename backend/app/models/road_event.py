from pydantic import BaseModel


class RoadEvent(BaseModel):
    road_name: str
    event_type: str
    severity: str
    description: str