from pydantic import BaseModel


class Ambulance(BaseModel):
    id: str
    driver: str
    status: str
    latitude: float
    longitude: float