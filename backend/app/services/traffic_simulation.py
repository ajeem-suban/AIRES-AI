import random


class TrafficSimulationService:

    def get_traffic_status(self):

        traffic = random.choice([
            "Light",
            "Moderate",
            "Heavy"
        ])

        if traffic == "Heavy":
            return {
                "traffic": traffic,
                "route": "Ring Road",
                "eta": 5,
                "rerouted": True
            }

        elif traffic == "Moderate":
            return {
                "traffic": traffic,
                "route": "Bypass Road",
                "eta": 6,
                "rerouted": True
            }

        return {
            "traffic": traffic,
            "route": "Main Road",
            "eta": 8,
            "rerouted": False
        }


traffic_simulation = TrafficSimulationService()