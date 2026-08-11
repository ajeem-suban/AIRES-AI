from app.services.state import active_dispatch
from app.services.hospital_service import recommend_hospital


def get_dashboard():

    ambulance = active_dispatch.get("ambulance")
    destination = active_dispatch.get("destination")

    if ambulance is None or destination is None:
        return {
            "message": "No active emergency"
        }

    hospital = recommend_hospital(
        destination["latitude"],
        destination["longitude"],
        "Cardiology"
    )

    return {
        "incoming_ambulance": {
            "id": ambulance["id"],
            "driver": ambulance["driver"],
            "status": "En Route"
        },
        "destination": destination,
        "recommended_hospital": hospital
    }