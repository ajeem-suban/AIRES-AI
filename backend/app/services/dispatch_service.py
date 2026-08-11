import json
from pathlib import Path

from app.models.ambulance import Ambulance
from app.models.dispatch import DispatchResponse
from app.utils.distance import calculate_distance
from app.services.state import active_dispatch

# Path to ambulances.json
DATA_FILE = Path(__file__).parent.parent / "data" / "ambulances.json"


def dispatch_ambulance(patient_lat: float, patient_lon: float):
    # Load ambulance data
    with open(DATA_FILE, "r") as file:
        ambulances = json.load(file)

    # Filter available ambulances
    available = [
        Ambulance(**ambulance)
        for ambulance in ambulances
        if ambulance["status"] == "Available"
    ]

    # No ambulance available
    if not available:
        return None

    # Find nearest ambulance
    nearest = min(
        available,
        key=lambda ambulance: calculate_distance(
            patient_lat,
            patient_lon,
            ambulance.latitude,
            ambulance.longitude,
        ),
    )

    # Calculate distance
    distance = calculate_distance(
        patient_lat,
        patient_lon,
        nearest.latitude,
        nearest.longitude,
    )

    # ⭐ Save active dispatch for tracking
    active_dispatch["ambulance"] = {
        "id": nearest.id,
        "driver": nearest.driver,
        "latitude": nearest.latitude,
        "longitude": nearest.longitude,
    }

    active_dispatch["destination"] = {
        "latitude": patient_lat,
        "longitude": patient_lon,
    }

    # Return dispatch response
    return DispatchResponse(
        ambulance_id=nearest.id,
        driver=nearest.driver,
        eta_minutes=max(1, int(distance * 120)),
        distance_km=round(distance * 111, 2),
        status="Dispatched",
    )