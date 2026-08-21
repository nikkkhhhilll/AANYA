"""
OpenStreetMap (OSM / OSRM) Distance & Dynamic Cab Fare Calculation Service.
Provides geo points, road distance calculations, and tiered fare algorithms:
- Hatchback: Base Rs.60 + Rs.20 per km
- Sedan: Base Rs.80 + Rs.22 per km
- SUV: Base Rs.100 + Rs.25 per km
"""
import math
import requests
import streamlit as st
from typing import Dict, Any, Tuple, Optional


# High-precision Geo Coordinates for GIM & Goa destinations
GOA_GEO_POINTS: Dict[str, Tuple[float, float]] = {
    "GIM Campus, Sanquelim": (15.5516, 74.0152),
    "Sanquelim Town": (15.5606, 74.0094),
    "Bicholim": (15.5925, 73.9536),
    "Mapusa": (15.5937, 73.8142),
    "Panjim (Panaji)": (15.4989, 73.8278),
    "Old Goa": (15.5009, 73.9116),
    "Calangute / Baga": (15.5528, 73.7517),
    "Anjuna / Vagator": (15.5847, 73.7438),
    "Candolim": (15.5186, 73.7681),
    "Goa Airport (Dabolim)": (15.3808, 73.8314),
    "Mopa Airport (MOPA)": (15.7725, 73.8686),
    "Thivim Railway Station": (15.6208, 73.8447),
    "Karmali Railway Station": (15.4872, 73.9189),
    "Madgaon (Margao)": (15.2736, 73.9744),
    "Palolem / South Goa": (15.0100, 74.0232),
}

# Pre-calibrated actual road distances (km) from GIM Campus (Sanquelim)
CALIBRATED_ROAD_DISTANCES: Dict[str, float] = {
    "GIM Campus, Sanquelim": 0.0,
    "Sanquelim Town": 2.5,
    "Bicholim": 9.0,
    "Mapusa": 26.0,
    "Panjim (Panaji)": 31.0,
    "Old Goa": 22.0,
    "Calangute / Baga": 37.0,
    "Anjuna / Vagator": 38.0,
    "Candolim": 39.0,
    "Goa Airport (Dabolim)": 51.0,
    "Mopa Airport (MOPA)": 42.0,
    "Thivim Railway Station": 22.5,
    "Karmali Railway Station": 25.0,
    "Madgaon (Margao)": 54.0,
    "Palolem / South Goa": 86.0,
}

# Dynamic Cab Fare Tier Rules
CAB_FARE_RULES: Dict[str, Dict[str, float]] = {
    "Hatchback": {"base_fare": 60.0, "rate_per_km": 20.0},
    "Sedan": {"base_fare": 80.0, "rate_per_km": 22.0},
    "SUV": {"base_fare": 100.0, "rate_per_km": 25.0},
    "Standard Cab": {"base_fare": 80.0, "rate_per_km": 22.0}, # default to sedan
}


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate Great Circle distance between two points in km."""
    R = 6371.0 # Earth's radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0)**2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


class DistanceService:
    """Service handling OSM distance routing and tiered fare calculation."""

    @staticmethod
    @st.cache_data(ttl=300)
    def get_route_distance(
        origin_name: str = "GIM Campus, Sanquelim",
        destination_name: str = "Panjim (Panaji)"
    ) -> Tuple[float, float, str]:
        """
        Calculate driving distance (km) and estimated duration (minutes).
        Returns: (distance_km, duration_mins, source_provider)
        """
        # Check calibrated table first for instant sub-millisecond response
        if destination_name in CALIBRATED_ROAD_DISTANCES and origin_name == "GIM Campus, Sanquelim":
            dist = CALIBRATED_ROAD_DISTANCES[destination_name]
            dur = max(5.0, round(dist * 1.4, 0)) # approx avg 45 km/h in Goa
            return dist, dur, "OpenStreetMap Calibrated"

        orig_coords = GOA_GEO_POINTS.get(origin_name, (15.5516, 74.0152))
        dest_coords = GOA_GEO_POINTS.get(destination_name)

        if not dest_coords:
            # Fallback estimation for custom destinations
            return 30.0, 45.0, "Default Estimate"

        # Try Live OSRM (Open Source Routing Machine) Routing API
        try:
            url = f"http://router.project-osrm.org/route/v1/driving/{orig_coords[1]},{orig_coords[0]};{dest_coords[1]},{dest_coords[0]}?overview=false"
            res = requests.get(url, timeout=1.5)
            if res.status_code == 200:
                data = res.json()
                if data.get("code") == "Ok" and data.get("routes"):
                    route = data["routes"][0]
                    dist_km = round(route["distance"] / 1000.0, 1)
                    dur_mins = round(route["duration"] / 60.0, 0)
                    return dist_km, dur_mins, "OpenStreetMap Live OSRM"
        except Exception:
            pass

        # Haversine with Goa mountain/coastal road curvature factor (~1.32)
        great_circle = haversine_distance_km(orig_coords[0], orig_coords[1], dest_coords[0], dest_coords[1])
        road_dist = round(great_circle * 1.32, 1)
        dur_mins = round(road_dist * 1.4, 0)
        return road_dist, dur_mins, "OpenStreetMap Geometry"

    @staticmethod
    def calculate_fare(distance_km: float, vehicle_type: str) -> Dict[str, Any]:
        """
        Compute cab fare using the exact pricing formula:
        - Hatchback: Base Rs.60 + Rs.20 per km
        - Sedan: Base Rs.80 + Rs.22 per km
        - SUV: Base Rs.100 + Rs.25 per km
        """
        # Normalize vehicle type
        tier = "Sedan"
        if "Hatchback" in vehicle_type or "Swift" in vehicle_type or "Aura" in vehicle_type:
            tier = "Hatchback"
        elif "SUV" in vehicle_type or "Innova" in vehicle_type or "Ertiga" in vehicle_type or "Thar" in vehicle_type or "7-Seater" in vehicle_type:
            tier = "SUV"
        elif "Sedan" in vehicle_type or "Dzire" in vehicle_type or "City" in vehicle_type:
            tier = "Sedan"

        from src.services.pricing_service import PricingService
        cab_rules = PricingService.get_cab_fare_rules()
        rule = cab_rules.get(tier, cab_rules.get("Sedan", {"base_fare": 80.0, "rate_per_km": 22.0}))
        base_fare = rule["base_fare"]
        rate_per_km = rule["rate_per_km"]

        distance_fare = rate_per_km * distance_km
        total_fare = round(base_fare + distance_fare, 0)

        return {
            "vehicle_tier": tier,
            "base_fare": base_fare,
            "rate_per_km": rate_per_km,
            "distance_km": distance_km,
            "distance_fare": round(distance_fare, 2),
            "total_fare": total_fare,
            "formula_string": f"₹{base_fare:.0f} Base + ({distance_km} km × ₹{rate_per_km:.0f}/km) = ₹{total_fare:,.0f}"
        }

    @staticmethod
    def get_all_destination_names() -> list:
        """List all supported destination names."""
        return [k for k in GOA_GEO_POINTS.keys() if k != "GIM Campus, Sanquelim"]
