from pydantic import BaseModel

class Hospital(BaseModel):
    id: str
    name: str
    latitude: float
    longitude: float
    beds_available: int
    icu_available: bool
    specialties: list[str]