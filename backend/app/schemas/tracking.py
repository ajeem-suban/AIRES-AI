from pydantic import BaseModel
from datetime import datetime


class TrackingLocation(BaseModel):
    ambulance_id: str
    latitude: float
    longitude: float
    speed_kmh: float
    timestamp: datetime