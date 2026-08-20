"""
Grievance and Complaint Resolution Service for GIM Campus Mobility.
Handles dispute ticketing, severity classification, and campus admin resolution workflows.
"""
import uuid
import datetime
import streamlit as st
from typing import Optional, Dict, Any, List, Tuple
from src.config import ComplaintType, ComplaintStatus, ComplaintPriority
from src.db import DBService


class ComplaintService:
    """Service handling grievance tickets, escalations, and resolution notes."""

    @staticmethod
    def file_complaint(
        raised_by_id: str,
        complaint_type: str,
        description: str,
        booking_id: Optional[str] = None,
        target_user_id: Optional[str] = None,
        priority: str = ComplaintPriority.MEDIUM.value
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Submit a formal grievance against a trip or provider."""
        if not description or not description.strip():
            return False, "Please describe the issue in detail.", None

        # Auto-resolve booking and target user if not specified
        if not booking_id:
            user_bookings = DBService.query("bookings", filters={"student_id": raised_by_id}, order_by="-created_at", limit=1)
            if user_bookings:
                booking_id = user_bookings[0]["id"]
                target_user_id = user_bookings[0].get("provider_id")
            else:
                # Fallback to any active booking
                any_bookings = DBService.query("bookings", limit=1)
                booking_id = any_bookings[0]["id"] if any_bookings else None

        if booking_id and not target_user_id:
            b_info = DBService.get_by_id("bookings", booking_id)
            if b_info:
                target_user_id = b_info.get("provider_id")

        new_id = str(uuid.uuid4())
        data = {
            "id": new_id,
            "booking_id": booking_id,
            "raised_by_id": raised_by_id,
            "target_user_id": target_user_id,
            "complaint_type": complaint_type,
            "description": description.strip(),
            "status": ComplaintStatus.OPEN.value,
            "priority": priority,
            "admin_notes": "",
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
        try:
            DBService.insert("complaints", data)
            from src.services.analytics_service import AnalyticsService
            AnalyticsService.log_event("complaint_filed", user_id=raised_by_id, metadata={"ticket_id": new_id, "type": complaint_type})
            return True, "Ticket raised successfully! The Campus Transport Committee has been notified.", data
        except Exception as e:
            return False, f"Failed to submit complaint: {e}", None

    @staticmethod
    def get_all_complaints() -> List[Dict[str, Any]]:
        """Fetch all complaints enriched with user and booking metadata."""
        complaints = DBService.query("complaints", order_by="-created_at")
        profiles = {p["id"]: p for p in DBService.query("profiles")}
        bookings = {b["id"]: b for b in DBService.query("bookings")}
        
        enriched = []
        for c in complaints:
            item = dict(c)
            raised_by = profiles.get(c.get("raised_by_id"), {})
            target = profiles.get(c.get("target_user_id"), {})
            booking = bookings.get(c.get("booking_id"), {})

            item["raised_by_name"] = raised_by.get("full_name", "Unknown")
            item["raised_by_email"] = raised_by.get("email", "")
            item["raised_by_phone"] = raised_by.get("phone", "")
            item["target_name"] = target.get("full_name", "N/A")
            item["service_segment"] = booking.get("service_segment", "N/A")
            item["pickup_location"] = booking.get("pickup_location", "N/A")
            item["dropoff_location"] = booking.get("dropoff_location", "N/A")
            enriched.append(item)
        return enriched

    @staticmethod
    def get_student_complaints(student_id: str) -> List[Dict[str, Any]]:
        """Fetch grievances raised by a specific student."""
        all_c = ComplaintService.get_all_complaints()
        return [c for c in all_c if c.get("raised_by_id") == student_id]

    @staticmethod
    def update_complaint_status(
        complaint_id: str,
        status: str,
        admin_notes: Optional[str] = None
    ) -> bool:
        """Update ticket resolution status and append admin notes."""
        updates: Dict[str, Any] = {"status": status}
        if admin_notes is not None:
            updates["admin_notes"] = admin_notes.strip()
        return DBService.update("complaints", complaint_id, updates)
