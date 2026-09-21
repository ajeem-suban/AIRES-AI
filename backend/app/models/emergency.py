from pydantic import BaseModel


class EmergencyRequest(BaseModel):
    caller_name: str
    phone_number: str
    emergency_type: str
    latitude: float
    longitude: float