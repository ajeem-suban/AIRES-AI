from fastapi import FastAPI

from app.routers import (
    routing,
    routing_ws,
    emergency,
    tracking,
    ws,
    hospital,
    hospital_dashboard
)

app = FastAPI(
    title="AIRES API",
    version="1.0.0"
)

app.include_router(routing_ws.router)
app.include_router(routing.router)
app.include_router(hospital_dashboard.router)
app.include_router(hospital.router)
app.include_router(emergency.router)
app.include_router(tracking.router)
app.include_router(ws.router)


@app.get("/")
def root():
    return {"message": "Welcome to AIRES 🚑"}