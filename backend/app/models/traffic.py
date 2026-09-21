from pydantic import BaseModel


class TrafficCondition(BaseModel):
    road_name: str
    congestion_level: str
    average_speed: float
    is_blocked: bool