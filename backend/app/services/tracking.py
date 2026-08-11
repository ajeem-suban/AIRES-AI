from datetime import datetime
from app.schemas.tracking import TrackingLocation


# Sample ambulance positions (MVP)
ambulance_locations = {
    "AMB001": {
        "latitude": 10.7905,
        "longitude": 78.7047,
        "speed_kmh": 55.0,
    },
    "AMB002": {
        "latitude": 10.7920,
        "longitude": 78.7060,
        "speed_kmh": 48.0,
    },
}


def get_location(ambulance_id: str) -> TrackingLocation:
    ambulance = ambulance_locations.get(ambulance_id)

    if ambulance is None:
        raise ValueError(f"Ambulance '{ambulance_id}' not found.")

    return TrackingLocation(
        ambulance_id=ambulance_id,
        latitude=ambulance["latitude"],
        longitude=ambulance["longitude"],
        speed_kmh=ambulance["speed_kmh"],
        timestamp=datetime.utcnow(),
    )


def update_location(ambulance_id: str) -> TrackingLocation:
    ambulance = ambulance_locations.get(ambulance_id)

    if ambulance is None:
        raise ValueError(f"Ambulance '{ambulance_id}' not found.")

    # Simulate movement
    ambulance["latitude"] = round(ambulance["latitude"] + 0.0001, 6)
    ambulance["longitude"] = round(ambulance["longitude"] + 0.0001, 6)

    return TrackingLocation(
        ambulance_id=ambulance_id,
        latitude=ambulance["latitude"],
        longitude=ambulance["longitude"],
        speed_kmh=ambulance["speed_kmh"],
        timestamp=datetime.utcnow(),
    )