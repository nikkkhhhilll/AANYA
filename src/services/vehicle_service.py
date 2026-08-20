"""
Vehicle & Route Management Service for GIM Mobility.
Provides dynamic cascading filters, fleet queries, route lookup, and provider KYC verification.
"""
import uuid
import datetime
import streamlit as st
from typing import Optional, Dict, Any, List, Tuple
from src.config import ServiceSegment, VehicleCategory, VehicleType
from src.db import DBService


class VehicleService:
    """Service handling fleet search, dynamic filters, routes, and provider status."""

    @staticmethod
    def get_standard_routes() -> List[Dict[str, Any]]:
        """Fetch standard predefined cab routes from/to GIM."""
        return DBService.query("standard_routes", order_by="destination")

    @staticmethod
    def get_all_vehicles() -> List[Dict[str, Any]]:
        """Fetch all vehicles with associated driver info."""
        import json
        vehicles = DBService.query("vehicles")
        drivers = {d["id"]: d for d in DBService.query("drivers")}
        profiles = {p["id"]: p for p in DBService.query("profiles")}

        enriched = []
        for v in vehicles:
            p_id = v.get("provider_id")
            driver_info = drivers.get(p_id, {})
            profile_info = profiles.get(p_id, {})
            
            v_copy = dict(v)
            if isinstance(v_copy.get("pricing_details"), str):
                try:
                    v_copy["pricing_details"] = json.loads(v_copy["pricing_details"])
                except Exception:
                    v_copy["pricing_details"] = {}
            elif not isinstance(v_copy.get("pricing_details"), dict):
                v_copy["pricing_details"] = {}

            v_copy["provider_name"] = profile_info.get("full_name", "Local Partner")
            v_copy["provider_phone"] = profile_info.get("phone", "+91 98000 00000")
            v_copy["business_name"] = driver_info.get("business_name") or profile_info.get("full_name")
            v_copy["is_verified"] = bool(driver_info.get("is_verified", False))
            v_copy["driver_rating"] = float(driver_info.get("rating", 5.0))
            v_copy["total_trips"] = int(driver_info.get("total_completed_trips", 0))
            v_copy["provider_available"] = bool(driver_info.get("is_available", True))
            enriched.append(v_copy)
        return enriched

    @staticmethod
    def get_vehicle_by_id(vehicle_id: str) -> Optional[Dict[str, Any]]:
        """Fetch enriched vehicle details by ID."""
        vehicles = VehicleService.get_all_vehicles()
        for v in vehicles:
            if v.get("id") == vehicle_id:
                return v
        return None

    @staticmethod
    def search_available_vehicles(
        segment: str,
        category: Optional[str] = None,
        vehicle_type: Optional[str] = None,
        min_passengers: int = 1,
        only_verified: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Dynamic search query builder with parameterized filtering (<2s target latency).
        For Cabs: available passenger seats is (seating_capacity - 1) since 1 seat is for the driver.
        For Self-Drive: available seats is full seating_capacity.
        """
        all_v = VehicleService.get_all_vehicles()
        results = []
        for v in all_v:
            # Must be active & available
            if not v.get("is_active") or not v.get("is_available"):
                continue
            if not v.get("provider_available"):
                continue
            if only_verified and not v.get("is_verified"):
                continue
            if segment and v.get("service_segment") != segment:
                continue
            if category and category != "All" and v.get("vehicle_category") != category:
                continue
            if vehicle_type and vehicle_type != "All" and v.get("vehicle_type") != vehicle_type:
                continue
            
            # Seating capacity filtering
            total_seats = int(v.get("seating_capacity", 4))
            if segment == "Cab":
                passenger_capacity = max(1, total_seats - 1) # n-1 seats available for passengers
            else:
                passenger_capacity = total_seats

            if passenger_capacity < min_passengers:
                continue

            results.append(v)
        return results

    @staticmethod
    def get_vehicles_by_provider(provider_id: str) -> List[Dict[str, Any]]:
        """Fetch all fleet vehicles belonging to a specific provider/driver."""
        return [v for v in VehicleService.get_all_vehicles() if v.get("provider_id") == provider_id]

    @staticmethod
    def add_vehicle(
        provider_id: str,
        service_segment: str,
        vehicle_category: str,
        vehicle_type: str,
        vehicle_model: str,
        vehicle_number: str,
        seating_capacity: int,
        pricing_details: Dict[str, Any]
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Add a new vehicle to the provider's fleet."""
        new_id = str(uuid.uuid4())
        record = {
            "id": new_id,
            "provider_id": provider_id,
            "service_segment": service_segment,
            "vehicle_category": vehicle_category,
            "vehicle_type": vehicle_type,
            "vehicle_model": vehicle_model.strip(),
            "vehicle_number": vehicle_number.strip().upper(),
            "seating_capacity": seating_capacity,
            "is_active": 1,
            "is_available": 1,
            "pricing_details": pricing_details,
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
        try:
            DBService.insert("vehicles", record)
            return True, "Vehicle registered successfully!", record
        except Exception as e:
            return False, f"Failed to register vehicle: {e}", None

    @staticmethod
    def update_vehicle_pricing(vehicle_id: str, pricing_details: Dict[str, Any]) -> bool:
        """Update vehicle pricing JSON details."""
        return DBService.update("vehicles", vehicle_id, {"pricing_details": pricing_details})

    @staticmethod
    def toggle_vehicle_availability(vehicle_id: str, is_available: bool) -> bool:
        """Toggle live vehicle availability state (<10s latency)."""
        return DBService.update("vehicles", vehicle_id, {"is_available": 1 if is_available else 0})

    @staticmethod
    def toggle_provider_availability(provider_id: str, is_available: bool) -> bool:
        """Toggle driver/provider duty status (Available vs Off-Duty)."""
        return DBService.update("drivers", provider_id, {"is_available": 1 if is_available else 0})

    @staticmethod
    def update_provider_verification(provider_id: str, is_verified: bool) -> bool:
        """Campus Admin KYC approval / rejection action."""
        return DBService.update("drivers", provider_id, {"is_verified": 1 if is_verified else 0})

    @staticmethod
    def get_all_drivers_kyc() -> List[Dict[str, Any]]:
        """Fetch all driver records enriched with profile info for Admin KYC review."""
        drivers = DBService.query("drivers")
        profiles = {p["id"]: p for p in DBService.query("profiles")}
        
        result = []
        for d in drivers:
            p = profiles.get(d["id"], {})
            item = dict(d)
            item["full_name"] = p.get("full_name", "Unknown")
            item["email"] = p.get("email", "")
            item["phone"] = p.get("phone", "")
            item["account_active"] = bool(p.get("is_active", 1))
            result.append(item)
        return result
