from fastapi import APIRouter

from app.services.hospital_dashboard_service import get_dashboard

router = APIRouter(
    prefix="/hospital-dashboard",
    tags=["Hospital Dashboard"]
)


@router.get("/")
def dashboard():
    return get_dashboard()