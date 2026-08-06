import logging
from typing import List, Dict, Any
import math

logger = logging.getLogger(__name__)

def calculate_distance(lat1, lon1, lat2, lng2):
    """Haversine formula to calculate distance between two points."""
    R = 6371e3 # meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lng2 - lon1)

    a = math.sin(delta_phi / 2)**2 + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def optimize_route(start_lat: float, start_lng: float, destinations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Solves a variation of the TSP using the Nearest Neighbor algorithm.
    start_lat/lng: Driver's current position.
    destinations: List of orders with their coordinates.
    """
    if not destinations:
        return []

    unvisited = destinations[:]
    optimized_path = []
    curr_lat, curr_lng = start_lat, start_lng

    while unvisited:
        # Find nearest point
        nearest = min(
            unvisited,
            key=lambda x: calculate_distance(curr_lat, curr_lng, x["latitude"], x["longitude"])
        )
        optimized_path.append(nearest)
        unvisited.remove(nearest)
        curr_lat, curr_lng = nearest["latitude"], nearest["longitude"]

    logger.info("Optimized route for %d destinations", len(optimized_path))
    return optimized_path
