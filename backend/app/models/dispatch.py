from pydantic import BaseModel


class DispatchResponse(BaseModel):
    ambulance_id: str
    driver: str
    eta_minutes: int
    distance_km: float
    status: str