import math

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate distance between two lat/lon coordinates using Haversine formula.
    Returns distance in meters.
    """
    R = 6371000  # Earth radius in meters

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (
        math.sin(dphi/2)**2 +
        math.cos(phi1) * math.cos(phi2) *
        math.sin(dlambda/2)**2
    )

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c
