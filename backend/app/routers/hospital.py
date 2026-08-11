from fastapi import APIRouter

from app.services.hospital_service import recommend_hospital

router = APIRouter(
    prefix="/hospital",
    tags=["Hospital"]
)


@router.get("/recommend")
def recommend(
    latitude: float,
    longitude: float,
    emergency_type: str
):
    return recommend_hospital(
        latitude,
        longitude,
        emergency_type
    )