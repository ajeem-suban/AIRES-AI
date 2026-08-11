from fastapi import APIRouter

from app.models.emergency import EmergencyRequest
from app.services.dispatch_service import dispatch_ambulance

router = APIRouter(
    prefix="/emergency",
    tags=["Emergency"]
)

@router.post("/call")
def emergency_call(request: EmergencyRequest):

    response = dispatch_ambulance(
        request.latitude,
        request.longitude
    )

    if response is None:
        return {
            "message": "No ambulance available"
        }

    return {
        "message": "Emergency received",
        "caller": request.caller_name,
        "ambulance": response
    }