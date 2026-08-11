from pydantic import BaseModel


class HospitalRequest(BaseModel):
    patient_latitude: float
    patient_longitude: float
    emergency_type: str


class HospitalInfo(BaseModel):
    id: str
    name: str
    beds_available: int
    icu_available: bool
    specialties: list[str]


class HospitalResponse(BaseModel):
    hospital: HospitalInfo
    distance_km: float
    estimated_time: str
    score: int
    reason: str