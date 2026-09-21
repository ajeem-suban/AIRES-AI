class EmergencyRequest(BaseModel):
    latitude: float
    longitude: float
    emergency_type: str
    severity: str