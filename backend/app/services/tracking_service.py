import asyncio

from app.services.state import active_dispatch


class AmbulanceTracker:

    def __init__(self):

        ambulance = active_dispatch["ambulance"]
        destination = active_dispatch["destination"]

        if ambulance is None or destination is None:
            raise ValueError("No active ambulance dispatch found.")

        self.latitude = ambulance["latitude"]
        self.longitude = ambulance["longitude"]

        self.target_lat = destination["latitude"]
        self.target_lon = destination["longitude"]

        self.ambulance_id = ambulance["id"]
        self.speed = 55

    async def track(self):

        while True:

            self.latitude += (self.target_lat - self.latitude) * 0.05
            self.longitude += (self.target_lon - self.longitude) * 0.05

            yield {
                "ambulance_id": self.ambulance_id,
                "latitude": round(self.latitude, 6),
                "longitude": round(self.longitude, 6),
                "speed": self.speed,
                "status": "En Route"
            }

            await asyncio.sleep(1)