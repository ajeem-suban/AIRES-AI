from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

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

# Demo only: let the dashboards call the API from any device
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

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


# Serves the dashboards at http://<laptop-ip>:8000/dashboards/
app.mount("/dashboards", StaticFiles(directory="frontend", html=True), name="dashboards")