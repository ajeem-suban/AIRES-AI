import math


def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Simple Euclidean distance for the MVP.
    We'll replace this with road-network routing later.
    """
    return math.sqrt((lat1 - lat2) ** 2 + (lon1 - lon2) ** 2)