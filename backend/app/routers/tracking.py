from fastapi import APIRouter

router = APIRouter(
    prefix="/tracking",
    tags=["Tracking"]
)


@router.get("/status")
def tracking_status():
    return {
        "message": "Tracking service ready"
    }