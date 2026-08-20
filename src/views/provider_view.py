"""
Driver and Rental Provider Portal View for GIM Campus Mobility.
Modern, clean, consumer-grade light theme (Uber/Airbnb Partner style).
Includes live availability toggle, incoming dispatch queue, fleet control, and 100% fare earnings.
"""
import streamlit as st
import pandas as pd
from typing import Dict, Any, List, Optional
from src.config import (
    ServiceSegment, VehicleCategory, VehicleType, BookingStatus,
    PriorityLevel, STATUS_COLORS, mask_phone_number, format_inr
)
from src.services.vehicle_service import VehicleService
from src.services.booking_service import BookingService
from src.services.analytics_service import AnalyticsService


def render_provider_portal(provider: Dict[str, Any]):
    """Render Driver/Provider operations dashboard in vibrant light theme."""
    provider_id = provider.get("id")
    provider_name = provider.get("full_name", "Partner")
    provider_phone = provider.get("phone", "")

    # Fetch provider driver record
    try:
        drivers_list = VehicleService.get_all_drivers_kyc()
        driver_record = next((d for d in drivers_list if d["id"] == provider_id), None)
    except Exception:
        driver_record = None
    
    business_name = driver_record.get("business_name") if driver_record else provider_name
    is_verified = driver_record.get("is_verified", False) if driver_record else False
    rating = driver_record.get("rating", 5.0) if driver_record else 5.0
    total_trips = driver_record.get("total_completed_trips", 0) if driver_record else 0
    is_available = driver_record.get("is_available", True) if driver_record else True

    # Modern Header Card
    verification_badge = '<span class="badge-verified">✓ Verified Campus Partner</span>' if is_verified else '<span class="badge-urgent">⏳ Pending Admin KYC</span>'

    st.markdown(f"""
    <div class="gim-hero">
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
            <div>
                <span style="font-size:0.75rem; text-transform:uppercase; letter-spacing:0.06em; color:#DBEAFE; font-weight:700;">Partner & Driver Console</span>
                <h2 style="margin:2px 0; font-size:1.8rem; font-weight:800; color:#FFFFFF;">{business_name}</h2>
                <p style="margin:4px 0 0 0; font-size:0.9rem; color:#DBEAFE;">{provider_name} • {verification_badge} • ⭐ <strong>{rating:.1f}/5.0</strong> ({total_trips} completed rides)</p>
            </div>
            <div style="background:rgba(255,255,255,0.18); border:1px solid rgba(255,255,255,0.3); border-radius:12px; padding:10px 18px; text-align:center;">
                <span style="font-size:0.75rem; color:#DBEAFE; text-transform:uppercase; font-weight:700;">Zero Commission Model</span><br/>
                <span style="font-size:1.3rem; font-weight:800; color:#FFFFFF;">100% Payout</span><br/>
                <span style="font-size:0.75rem; color:#A7F3D0; font-weight:600;">You retain 100% of trip fares</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 1. Live Duty Status Control
    st.markdown("### 🟢 Duty & Availability Status")
    col_stat1, col_stat2 = st.columns([1, 2])
    with col_stat1:
        current_status_label = "Available (Accepting Rides)" if is_available else "Off-Duty / Unavailable"
        new_avail = st.toggle("Online for Campus Bookings", value=is_available, key="driver_duty_toggle")
        if new_avail != is_available:
            try:
                VehicleService.toggle_provider_availability(provider_id, new_avail)
                st.toast(f"Status updated: {'Online & Accepting Rides' if new_avail else 'Off-Duty'}", icon="🟢" if new_avail else "⚪")
                st.rerun()
            except Exception:
                st.toast("Could not update status. Please try again.", icon="⚠️")

    with col_stat2:
        st.markdown(f"""
        <div style="background:#FFFFFF; padding:12px 16px; border-radius:10px; border:1px solid #E2E8F0; border-left:4px solid {'#10B981' if is_available else '#EF4444'}; box-shadow:0 2px 4px rgba(0,0,0,0.03);">
            Current Status: <strong>{current_status_label}</strong><br/>
            <span style="font-size:0.8rem; color:#64748B;">When online, students can immediately discover and book your vehicles.</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

    # Navigation Sub-tabs
    tab_queue, tab_fleet, tab_earnings = st.tabs([
        "📥 Active & Incoming Bookings",
        "🚙 Vehicle Inventory",
        "💰 Payouts & Earnings"
    ])

    with tab_queue:
        render_dispatch_queue(provider_id)

    with tab_fleet:
        render_fleet_management(provider_id)

    with tab_earnings:
        render_earnings_tab(provider_id)


def render_dispatch_queue(provider_id: str):
    """Real-time incoming ride/rental requests."""
    st.markdown("### 📥 Active & Incoming Dispatches")

    try:
        bookings = BookingService.get_provider_bookings(provider_id)
        active_trips = [b for b in bookings if b.get("booking_status") in (BookingStatus.REQUESTED.value, BookingStatus.CONFIRMED.value, BookingStatus.IN_PROGRESS.value)]
    except Exception:
        active_trips = []

    if not active_trips:
        st.info("No active dispatches right now. As soon as a student books your cab or rental vehicle, it will appear here.")
        return

    for trip in active_trips:
        trip_id = trip["id"]
        status = trip.get("booking_status", "confirmed")
        with st.container():
            col_d1, col_d2, col_d3 = st.columns([2.5, 1.2, 1.3])

            with col_d1:
                st.markdown(f"""
                <div style="font-size:1.15rem; font-weight:700; color:#0F172A;">📍 {trip.get('pickup_location')} ➔ {trip.get('dropoff_location')}</div>
                <div style="font-size:0.85rem; color:#64748B; margin-top:2px;">
                    Student: <strong>{trip.get('student_name', 'Student')}</strong> (📞 {trip.get('student_phone', '')})<br/>
                    Vehicle: <strong>{trip.get('vehicle_model')}</strong> ({trip.get('vehicle_number')})
                </div>
                """, unsafe_allow_html=True)

            with col_d2:
                st.markdown(f"""
                <div style="text-align:right;">
                    <div style="font-size:1.3rem; font-weight:800; color:#059669;">{format_inr(trip.get('base_trip_fare', 0))}</div>
                    <span style="font-size:0.75rem; color:#64748B;">100% Direct Payout</span>
                </div>
                """, unsafe_allow_html=True)

            with col_d3:
                if status in ("requested", "confirmed"):
                    if st.button("Mark In Progress", key=f"prog_{trip_id}", use_container_width=True):
                        BookingService.update_booking_status(trip_id, BookingStatus.IN_PROGRESS.value)
                        st.toast("Trip started!", icon="🚀")
                        st.rerun()
                elif status == "in_progress":
                    if st.button("Complete Trip", key=f"comp_{trip_id}", use_container_width=True, type="primary"):
                        BookingService.update_booking_status(trip_id, BookingStatus.COMPLETED.value)
                        st.toast("Trip marked completed!", icon="🎉")
                        st.rerun()

            st.divider()


def render_fleet_management(provider_id: str):
    """Fleet status management."""
    st.markdown("### 🚙 Your Registered Fleet")
    try:
        vehicles = VehicleService.get_provider_vehicles(provider_id)
    except Exception:
        vehicles = []

    if not vehicles:
        st.info("No vehicles registered under your profile yet.")
        return

    for v in vehicles:
        v_id = v["id"]
        is_avail = bool(v.get("is_available", True))

        col_f1, col_f2 = st.columns([3, 1])
        with col_f1:
            st.markdown(f"""
            <strong>{v.get('vehicle_model')}</strong> ({v.get('vehicle_number')})<br/>
            <span style="font-size:0.8rem; color:#64748B;">Category: {v.get('vehicle_category')} • Type: {v.get('vehicle_type')} • {v.get('seating_capacity')} Seats</span>
            """, unsafe_allow_html=True)
        with col_f2:
            new_v_avail = st.toggle("Active", value=is_avail, key=f"v_toggle_{v_id}")
            if new_v_avail != is_avail:
                VehicleService.update_vehicle_availability(v_id, new_v_avail)
                st.toast(f"Vehicle {'enabled' if new_v_avail else 'disabled'}")
                st.rerun()
        st.divider()


def render_earnings_tab(provider_id: str):
    """Partner earnings ledger."""
    st.markdown("### 💰 Direct Earnings & Payouts")
    try:
        bookings = BookingService.get_provider_bookings(provider_id)
        completed = [b for b in bookings if b.get("booking_status") == BookingStatus.COMPLETED.value]
    except Exception:
        completed = []

    total_earned = sum(float(b.get("base_trip_fare", 0)) for b in completed)

    col_e1, col_e2 = st.columns(2)
    with col_e1:
        st.metric("Total Trips Completed", len(completed))
    with col_e2:
        st.metric("Total Direct Earnings (100% Payout)", format_inr(total_earned))

    st.caption("All trip fares are paid directly to your UPI/Bank with zero platform commission deductions.")
