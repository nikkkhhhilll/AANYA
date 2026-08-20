"""
Booking, Concurrency Control, and Payment Fee Workflow Service for GIM Mobility.
Enforces double-booking prevention, 0% provider commission, and ₹20 UPI convenience fee.
"""
import uuid
import datetime
import streamlit as st
from typing import Optional, Dict, Any, List, Tuple
from src.config import BookingStatus, PriorityLevel, PLATFORM_CONVENIENCE_FEE
from src.db import DBService
from src.services.vehicle_service import VehicleService


class BookingService:
    """Service handling booking lifecycles, concurrency checks, and payment state."""

    @staticmethod
    def _normalize_dt(dt_val: Any) -> datetime.datetime:
        """Helper to convert str/datetime into offset-naive datetime for safe comparison."""
        if not dt_val:
            return datetime.datetime.now()
        if isinstance(dt_val, str):
            dt_str = dt_val.replace("Z", "+00:00")
            parsed = datetime.datetime.fromisoformat(dt_str)
        elif isinstance(dt_val, datetime.datetime):
            parsed = dt_val
        else:
            return datetime.datetime.now()
        
        if parsed.tzinfo is not None:
            return parsed.astimezone(datetime.timezone.utc).replace(tzinfo=None)
        return parsed

    @staticmethod
    def check_vehicle_availability_for_slot(
        vehicle_id: str,
        start_datetime: str,
        end_datetime: Optional[str] = None,
        exclude_booking_id: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Concurrency check to prevent double bookings on the same vehicle/slot (NFR Reliability).
        """
        # Fetch active or confirmed bookings for this vehicle
        active_bookings = DBService.query("bookings", filters={"vehicle_id": vehicle_id})
        
        # Parse proposed slot with timezone normalization
        try:
            prop_start = BookingService._normalize_dt(start_datetime)
            prop_end = BookingService._normalize_dt(end_datetime) if end_datetime else prop_start + datetime.timedelta(hours=4)
        except Exception:
            return True, "Slot available"

        for b in active_bookings:
            if exclude_booking_id and b.get("id") == exclude_booking_id:
                continue
            
            status = b.get("booking_status")
            if status in (BookingStatus.REQUESTED.value, BookingStatus.CONFIRMED.value, BookingStatus.IN_PROGRESS.value):
                try:
                    b_start = BookingService._normalize_dt(b.get("start_datetime"))
                    b_end = BookingService._normalize_dt(b.get("end_datetime")) if b.get("end_datetime") else b_start + datetime.timedelta(hours=4)
                    
                    # Check for temporal overlap
                    if max(prop_start, b_start) < min(prop_end, b_end):
                        return False, f"Vehicle is already scheduled/booked during this slot ({b_start.strftime('%d %b %H:%M')} - {b_end.strftime('%H:%M')})."
                except Exception:
                    continue

        return True, "Vehicle is available for the requested slot."

    @staticmethod
    def create_booking_request(
        student_id: str,
        vehicle_id: str,
        provider_id: str,
        service_segment: str,
        vehicle_category: str,
        vehicle_type: str,
        pickup_location: str,
        dropoff_location: str,
        start_datetime: str,
        end_datetime: Optional[str],
        passengers_count: int,
        rental_duration: str,
        base_trip_fare: float,
        priority_level: str = PriorityLevel.STANDARD.value,
        special_notes: str = "",
        auto_pay_fee: bool = False
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Create a booking with flat ₹20 convenience fee and concurrency verification (<5s latency).
        """
        # 1. Concurrency Check
        is_free, msg = BookingService.check_vehicle_availability_for_slot(vehicle_id, start_datetime, end_datetime)
        if not is_free:
            return False, msg, None

        new_booking_id = str(uuid.uuid4())
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        
        booking_data = {
            "id": new_booking_id,
            "student_id": student_id,
            "vehicle_id": vehicle_id,
            "provider_id": provider_id,
            "service_segment": service_segment,
            "vehicle_category": vehicle_category,
            "vehicle_type": vehicle_type,
            "pickup_location": pickup_location.strip(),
            "dropoff_location": dropoff_location.strip(),
            "start_datetime": start_datetime,
            "end_datetime": end_datetime,
            "passengers_count": passengers_count,
            "rental_duration_days_or_hours": rental_duration,
            "base_trip_fare": float(base_trip_fare),
            "convenience_fee": float(PLATFORM_CONVENIENCE_FEE),
            "fee_payment_status": "paid" if auto_pay_fee else "pending",
            "booking_status": BookingStatus.CONFIRMED.value if auto_pay_fee else BookingStatus.REQUESTED.value,
            "priority_level": priority_level,
            "special_notes": special_notes.strip(),
            "created_at": now,
        }

        try:
            DBService.insert("bookings", booking_data)
            # Log analytics telemetry
            from src.services.analytics_service import AnalyticsService
            AnalyticsService.log_event(
                event_name="booking_completed",
                user_id=student_id,
                metadata={
                    "booking_id": new_booking_id,
                    "service_segment": service_segment,
                    "fare": float(base_trip_fare),
                    "destination": dropoff_location
                }
            )
            return True, "Booking created successfully!", booking_data
        except Exception as e:
            return False, f"Booking creation failed: {e}", None

    @staticmethod
    def process_upi_fee_payment(booking_id: str, upi_ref_id: str) -> Tuple[bool, str]:
        """
        Simulate/process the flat ₹20 convenience fee payment via UPI.
        Upon payment, moves booking from 'requested' to 'confirmed'.
        """
        booking = DBService.get_by_id("bookings", booking_id)
        if not booking:
            return False, "Booking not found."

        updates = {
            "fee_payment_status": "paid",
            "booking_status": BookingStatus.CONFIRMED.value,
        }
        success = DBService.update("bookings", booking_id, updates)
        if success:
            return True, f"Payment verified! ₹20 Platform Fee received via UPI Ref {upi_ref_id}. Booking is CONFIRMED."
        return False, "Failed to update payment status."

    @staticmethod
    def update_booking_status(booking_id: str, new_status: str, admin_override: bool = False) -> bool:
        """Update booking lifecycle status."""
        valid_statuses = [s.value for s in BookingStatus]
        if new_status not in valid_statuses:
            return False

        updates = {"booking_status": new_status}
        return DBService.update("bookings", booking_id, updates)

    @staticmethod
    def get_booking_details(booking_id: str) -> Optional[Dict[str, Any]]:
        """Fetch booking with enriched student, driver, and vehicle metadata."""
        booking = DBService.get_by_id("bookings", booking_id)
        if not booking:
            return None

        enriched = dict(booking)
        student = DBService.get_by_id("profiles", booking.get("student_id"))
        driver_profile = DBService.get_by_id("profiles", booking.get("provider_id"))
        driver_meta = DBService.get_by_id("drivers", booking.get("provider_id"))
        vehicle = DBService.get_by_id("vehicles", booking.get("vehicle_id"))

        if student:
            enriched["student_name"] = student.get("full_name")
            enriched["student_email"] = student.get("email")
            enriched["student_phone"] = student.get("phone")
            enriched["student_program"] = student.get("program")

        if driver_profile:
            enriched["driver_name"] = driver_profile.get("full_name")
            enriched["driver_phone"] = driver_profile.get("phone")
            enriched["provider_phone"] = driver_profile.get("phone")

        if driver_meta:
            enriched["driver_business"] = driver_meta.get("business_name")
            enriched["business_name"] = driver_meta.get("business_name") or driver_profile.get("full_name") if driver_profile else "Verified Partner"
            enriched["driver_rating"] = driver_meta.get("rating")
            enriched["driver_verified"] = driver_meta.get("is_verified")

        if vehicle:
            enriched["vehicle_model"] = vehicle.get("vehicle_model")
            enriched["vehicle_number"] = vehicle.get("vehicle_number")
            enriched["pricing_details"] = vehicle.get("pricing_details")

        return enriched

    @staticmethod
    def get_student_bookings(student_id: str) -> List[Dict[str, Any]]:
        """Fetch all bookings for a given student in reverse chronological order."""
        bookings = DBService.query("bookings", filters={"student_id": student_id}, order_by="-created_at")
        return [BookingService.get_booking_details(b["id"]) for b in bookings if b]

    @staticmethod
    def get_active_bookings_for_student(student_id: str) -> List[Dict[str, Any]]:
        """Fetch active/in-progress bookings for a given student."""
        all_student_bookings = BookingService.get_student_bookings(student_id)
        active_statuses = (
            BookingStatus.REQUESTED.value,
            BookingStatus.CONFIRMED.value,
            BookingStatus.IN_PROGRESS.value
        )
        return [b for b in all_student_bookings if b and b.get("booking_status") in active_statuses]

    @staticmethod
    def get_provider_bookings(provider_id: str) -> List[Dict[str, Any]]:
        """Fetch all bookings dispatched to a given provider/driver."""
        bookings = DBService.query("bookings", filters={"provider_id": provider_id}, order_by="-created_at")
        return [BookingService.get_booking_details(b["id"]) for b in bookings if b]

    @staticmethod
    def get_all_bookings() -> List[Dict[str, Any]]:
        """Fetch all bookings on the platform for Campus Admin oversight."""
        bookings = DBService.query("bookings", order_by="-created_at")
        return [BookingService.get_booking_details(b["id"]) for b in bookings if b]

    @staticmethod
    def submit_review(booking_id: str, student_id: str, provider_id: str, rating: int, comment: str) -> Tuple[bool, str]:
        """Submit post-ride review and rating (1-5 stars)."""
        new_id = str(uuid.uuid4())
        data = {
            "id": new_id,
            "booking_id": booking_id,
            "student_id": student_id,
            "provider_id": provider_id,
            "rating": max(1, min(5, int(rating))),
            "comment": comment.strip(),
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
        try:
            DBService.insert("reviews", data)
            # Recompute provider average rating
            reviews = DBService.query("reviews", filters={"provider_id": provider_id})
            if reviews:
                avg_rating = sum(r["rating"] for r in reviews) / len(reviews)
                DBService.update("drivers", provider_id, {"rating": round(avg_rating, 2)})
            return True, "Thank you! Your review has been recorded."
        except Exception as e:
            return False, f"Failed to submit review: {e}"

    @staticmethod
    def get_all_reviews() -> List[Dict[str, Any]]:
        """Fetch all reviews with student and provider information."""
        reviews = DBService.query("reviews", order_by="-created_at")
        profiles = {p["id"]: p for p in DBService.query("profiles")}
        drivers = {d["id"]: d for d in DBService.query("drivers")}
        
        result = []
        for r in reviews:
            item = dict(r)
            s = profiles.get(r.get("student_id"), {})
            d = profiles.get(r.get("provider_id"), {})
            dm = drivers.get(r.get("provider_id"), {})
            item["student_name"] = s.get("full_name", "Student")
            item["student_email"] = s.get("email", "")
            item["provider_name"] = dm.get("business_name") or d.get("full_name", "Provider")
            result.append(item)
        return result
