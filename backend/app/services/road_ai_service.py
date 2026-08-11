import random

ROAD_EVENTS = [

    {
        "road_name": "Main Road",
        "event_type": "Clear",
        "severity": "Low",
        "description": "Road is clear."
    },

    {
        "road_name": "Main Road",
        "event_type": "Traffic Jam",
        "severity": "Medium",
        "description": "Heavy traffic detected."
    },

    {
        "road_name": "Main Road",
        "event_type": "Construction",
        "severity": "High",
        "description": "Road construction ahead."
    },

    {
        "road_name": "Main Road",
        "event_type": "Accident",
        "severity": "Critical",
        "description": "Major accident blocking road."
    },

    {
        "road_name": "Main Road",
        "event_type": "Flood",
        "severity": "Critical",
        "description": "Flooded road detected."
    }

]


class RoadAIService:

    def detect_event(self):
        return random.choice(ROAD_EVENTS)


road_ai_service = RoadAIService()