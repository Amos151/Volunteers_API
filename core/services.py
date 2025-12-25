from __future__ import annotations
from dataclasses import dataclass
from math import radians, sin, cos, sqrt, atan2
from typing import Optional, Tuple
from geopy.geocoders import Nominatim

_geolocator = Nominatim(user_agent="volunteers_api")

def geocode_location(text: str) -> Tuple[Optional[float], Optional[float]]:
    if not text:
        return (None, None)
    try:
        loc = _geolocator.geocode(text, timeout=10)
        if not loc:
            return (None, None)
        return (float(loc.latitude), float(loc.longitude))
    except Exception:
        return (None, None)

def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c
