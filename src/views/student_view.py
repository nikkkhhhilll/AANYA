"""
Student Portal View for GIM Campus Mobility.
Modern, clean, consumer-grade light theme (Uber/Airbnb style).
Features dynamic Cabs/Self-Drive search, rectangular service tabs, transparent pricing, instant booking confirmation modal, active trip tracking, and dispute ticketing.
"""
import datetime
import streamlit as st
import pandas as pd
from typing import Dict, Any, List, Optional
from src.config import (
    ServiceSegment, VehicleCategory, VehicleType, BookingStatus,
    PriorityLevel, ComplaintType, PLATFORM_CONVENIENCE_FEE,
    STATUS_COLORS, mask_phone_number, format_inr, SELF_DRIVE_HOURLY_RATES
)
from src.services.vehicle_service import VehicleService
from src.services.booking_service import BookingService
from src.services.complaint_service import ComplaintService
from src.services.analytics_service import AnalyticsService
from src.services.distance_service import DistanceService


def render_student_portal(student: Dict[str, Any]):
    """Render main consumer-grade student mobility interface."""
    student_id = student.get("id")
    student_name = student.get("full_name", "Student")
    student_email = student.get("email", "")
    student_program = student.get("program", "PGDM")

    # Header Card
    st.markdown(f"""
    <div class="gim-hero">
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
            <div>
                <h2 style="margin:0; font-size:1.8rem; font-weight:800; color:#FFFFFF;">Campus Mobility</h2>
                <p style="margin:4px 0 0 0; font-size:0.95rem; color:#DBEAFE;">
                    Welcome, <strong>{student_name}</strong> • {student_program}
                </p>
            </div>
            <div style="background:rgba(255,255,255,0.18); border-radius:12px; padding:6px 14px; border:1px solid rgba(255,255,255,0.3);">
                <span style="font-size:0.75rem; color:#DBEAFE; text-transform:uppercase; letter-spacing:0.04em;">Verified Campus ID</span><br/>
                <span style="font-size:0.9rem; color:#FFFFFF; font-weight:600;">✓ {student_email}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Toast notification if booking was just made
    if st.session_state.get("booking_just_confirmed"):
        st.toast("🎉 Booking confirmed! Your driver details are now active.", icon="✅")
        st.session_state["booking_just_confirmed"] = False

    # Log page view telemetry
    try:
        AnalyticsService.log_event("page_view", user_id=student_id, metadata={"portal": "student_view"})
    except Exception:
        pass

    # Fetch active bookings for dynamic tab counter & top banner
    try:
        active_bookings = BookingService.get_active_bookings_for_student(student_id)
    except Exception:
        active_bookings = []

    # Active Trip Notification Banner (Visible immediately across all tabs)
    if active_bookings:
        latest = active_bookings[0]
        latest_phone = latest.get("provider_phone") or latest.get("driver_phone") or "+91 98221 55667"
        latest_driver = latest.get("business_name") or latest.get("driver_name") or "Verified Driver"
        st.markdown(f"""
        <div style="background: #F0FDF4; border: 1px solid #86EFAC; border-radius: 12px; padding: 14px 18px; margin-bottom: 18px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; box-shadow: 0 2px 4px rgba(22, 101, 52, 0.05);">
            <div>
                <span style="background: #DCFCE7; color: #166534; font-weight: 700; font-size: 0.75rem; padding: 3px 10px; border-radius: 9999px; text-transform: uppercase; letter-spacing: 0.04em;">
                    🟢 Active Ride Pass (#{latest['id'][:8]})
                </span>
                <div style="font-size: 1.1rem; font-weight: 700; color: #0F172A; margin: 6px 0 2px 0;">
                    📍 {latest.get('pickup_location')} ➔ {latest.get('dropoff_location')}
                </div>
                <div style="font-size: 0.85rem; color: #374151;">
                    Driver: <strong>{latest_driver}</strong> • 📞 <strong>{latest_phone}</strong> • Vehicle: <strong>{latest.get('vehicle_model')}</strong> ({latest.get('vehicle_number')})
                </div>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 1.3rem; font-weight: 800; color: #15803D;">{format_inr(latest.get('base_trip_fare', 0))}</div>
                <span style="font-size: 0.75rem; color: #166534; font-weight: 600;">✓ Confirmed at Gate 2</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    active_tab_title = f"📍 Active Trips ({len(active_bookings)})" if active_bookings else "📍 Active Trips"

    # Navigation Tabs
    tab_book, tab_active, tab_history, tab_help = st.tabs([
        "🚗 Book a Ride",
        active_tab_title,
        "📜 Past Trips & Reviews",
        "💬 Help & Support"
    ])

    with tab_book:
        render_booking_section(student)

    with tab_active:
        render_active_bookings_section(student, active_bookings)

    with tab_history:
        render_history_section(student)

    with tab_help:
        render_grievance_section(student)


def render_booking_section(student: Dict[str, Any]):
    """Dynamic ride & rental search with rectangular full-width tabs."""
    service_tabs = st.tabs(["Cabs (Chauffeured)", "Self-Drive Rentals (Cars & Bikes)"])

    with service_tabs[0]:
        render_cab_booking_flow(student)

    with service_tabs[1]:
        render_self_drive_booking_flow(student)


def render_cab_booking_flow(student: Dict[str, Any]):
    """Chauffeured cab booking interface with clean route calculations."""
    pickup_loc = "GIM Gate No. 2"

    # Pickup Point highlighted as a clean note
    st.markdown("""
    <div style="font-size:0.82rem; color:#2563EB; font-weight:600; margin-bottom:12px; display:flex; align-items:center; gap:6px;">
        <span>📍</span> <span><strong>Campus Pickup Point:</strong> All verified cabs pick up directly at <strong>GIM Gate No. 2</strong>.</span>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([3, 1])

    destination_list = DistanceService.get_all_destination_names()
    route_options = destination_list + ["Custom Destination / Other"]

    with col1:
        selected_dest = st.selectbox("Where to?", route_options, index=3, key="cab_dest_sel")

    custom_dest = ""
    if selected_dest == "Custom Destination / Other":
        custom_dest = st.text_input("Enter Destination", placeholder="e.g. Mandrem Beach, North Goa", key="cab_custom_dest")

    final_dest = custom_dest.strip() if selected_dest == "Custom Destination / Other" and custom_dest.strip() else selected_dest

    with col2:
        passengers_count = st.selectbox(
            "Passengers",
            [1, 2, 3, 4, 5, 6],
            index=0,
            format_func=lambda x: f"{x} Rider" if x == 1 else f"{x} Riders",
            key="cab_pax_count"
        )

    # Route Distance Calculation
    try:
        calc_dest = selected_dest if selected_dest != "Custom Destination / Other" else "Panjim (Panaji)"
        distance_km, duration_mins, route_desc = DistanceService.get_route_distance("GIM Campus, Sanquelim", calc_dest)
    except Exception:
        distance_km, duration_mins = 31.0, 45

    # Compact Route Summary Bar
    st.markdown(f"""
    <div class="route-badge-bar">
        <span>📍 <strong>GIM Gate 2</strong> ➔ <strong>{final_dest}</strong></span>
        <span style="color:#2563EB;"><strong>{distance_km:.1f} km</strong> • ~{duration_mins} mins travel</span>
    </div>
    """, unsafe_allow_html=True)

    # Query Available Verified Cabs
    try:
        available_cabs = VehicleService.search_available_vehicles(
            segment=ServiceSegment.CAB.value,
            min_passengers=passengers_count,
            only_verified=True
        )
    except Exception:
        available_cabs = []

    if not available_cabs:
        st.info("No verified cabs available matching the selected passenger count. Please try a different capacity.")
        return

    st.markdown(f"#### Available Cabs ({len(available_cabs)})")

    # Render vehicle options as interactive cards
    for cab in available_cabs:
        tier = cab.get("vehicle_type", "Sedan")
        if tier not in ["Hatchback", "Sedan", "SUV"]:
            tier = "Sedan"

        fare_calc = DistanceService.calculate_fare(distance_km, tier)
        trip_fare = fare_calc["total_fare"]
        rate_km = fare_calc["rate_per_km"]

        # Passenger seat capacity = seating_capacity - 1
        total_seats = int(cab.get("seating_capacity", 4))
        pax_capacity = max(1, total_seats - 1)

        tier_tag = {
            "Hatchback": ("Eco Choice", "#D1FAE5", "#065F46"),
            "Sedan": ("Comfort", "#EFF6FF", "#1D4ED8"),
            "SUV": ("Spacious Group", "#FEF3C7", "#92400E")
        }.get(tier, ("Standard", "#F1F5F9", "#475569"))

        with st.container():
            col_v1, col_v2, col_v3 = st.columns([2.5, 1.2, 1.3])

            with col_v1:
                st.markdown(f"""
                <div style="display:flex; align-items:center; gap:10px;">
                    <span style="font-size:1.15rem; font-weight:700; color:#0F172A;">{cab.get('vehicle_model')}</span>
                    <span style="background:{tier_tag[1]}; color:{tier_tag[2]}; padding:2px 8px; border-radius:9999px; font-size:0.75rem; font-weight:600;">{tier_tag[0]}</span>
                </div>
                <div style="font-size:0.85rem; color:#64748B; margin-top:2px;">
                    💺 {pax_capacity} Passenger Seats • Driver: <strong>{cab.get('business_name')}</strong> • ⭐ {cab.get('driver_rating', 5.0):.1f} ({cab.get('total_trips', 0)} trips)
                </div>
                """, unsafe_allow_html=True)

            with col_v2:
                st.markdown(f"""
                <div style="text-align:right;">
                    <div style="font-size:1.3rem; font-weight:800; color:#0F172A;">{format_inr(trip_fare)}</div>
                    <div style="font-size:0.75rem; color:#64748B;">₹{rate_km:.0f}/km • 0% driver cut</div>
                </div>
                """, unsafe_allow_html=True)

            with col_v3:
                if st.button("Select & Book", key=f"book_cab_{cab['id']}", use_container_width=True, type="primary"):
                    try:
                        AnalyticsService.log_event("booking_started", user_id=student["id"], metadata={"vehicle_id": cab["id"], "fare": trip_fare, "segment": "Cab"})
                    except Exception:
                        pass
                    trip_ctx = {
                        "pickup": pickup_loc,
                        "dropoff": final_dest,
                        "distance_km": distance_km,
                        "base_trip_fare": trip_fare,
                        "passengers": passengers_count,
                        "duration": f"~{duration_mins} mins",
                        "start_dt": datetime.datetime.now().isoformat(),
                        "end_dt": (datetime.datetime.now() + datetime.timedelta(minutes=duration_mins)).isoformat()
                    }
                    show_booking_confirmation_dialog(cab, student, trip_ctx)

            st.divider()


def render_self_drive_booking_flow(student: Dict[str, Any]):
    """Cascading self-drive car and bike rentals."""
    st.caption("Drive yourself across Goa with transparent hourly rates. Zero security lockups.")

    col_c1, col_c2, col_c3 = st.columns(3)

    with col_c1:
        chosen_cat = st.selectbox(
            "1. Vehicle Category",
            [VehicleCategory.FOUR_WHEELER.value, VehicleCategory.TWO_WHEELER.value],
            format_func=lambda x: "🚗 4-Wheeler (Cars)" if x == VehicleCategory.FOUR_WHEELER.value else "🛵 2-Wheeler (Bikes & Scooties)",
            key="sd_cat_sel"
        )

    with col_c2:
        if chosen_cat == VehicleCategory.FOUR_WHEELER.value:
            type_options = ["All", VehicleType.HATCHBACK.value, VehicleType.SEDAN.value, VehicleType.SUV.value]
        else:
            type_options = ["All", VehicleType.SCOOTY.value, VehicleType.BIKE.value]

        chosen_type = st.selectbox("2. Vehicle Type", type_options, key="sd_type_sel")

    with col_c3:
        if chosen_cat == VehicleCategory.TWO_WHEELER.value:
            pax_options = [1, 2]
        elif chosen_type == VehicleType.SUV.value:
            pax_options = [1, 2, 3, 4, 5, 6, 7]
        else:
            pax_options = [1, 2, 3, 4, 5]

        pax_count = st.selectbox(
            "3. Passengers Count",
            pax_options,
            index=0,
            format_func=lambda x: f"{x} Person" if x == 1 else f"{x} Persons",
            key="sd_pax_filter"
        )

    # Schedule Duration Picker
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        pickup_date = st.date_input("Pickup Date", datetime.date.today(), key="sd_pickup_date")
        pickup_time = st.time_input("Pickup Time", datetime.time(9, 0), key="sd_pickup_time")
    with col_d2:
        return_date = st.date_input("Return Date", datetime.date.today() + datetime.timedelta(days=1), key="sd_return_date")
        return_time = st.time_input("Return Time", datetime.time(18, 0), key="sd_return_time")

    start_dt = datetime.datetime.combine(pickup_date, pickup_time)
    end_dt = datetime.datetime.combine(return_date, return_time)

    if end_dt <= start_dt:
        st.warning("⚠️ Return time must be after the pickup time.")
        return

    duration_hours = max(1.0, (end_dt - start_dt).total_seconds() / 3600.0)

    # Search Fleet
    type_filter = None if chosen_type == "All" else chosen_type
    try:
        vehicles = VehicleService.search_available_vehicles(
            segment=ServiceSegment.SELF_DRIVE.value,
            category=chosen_cat,
            vehicle_type=type_filter,
            min_passengers=pax_count,
            only_verified=True
        )
    except Exception:
        vehicles = []

    st.markdown(f"#### Available Fleet ({len(vehicles)}) • Duration: **{duration_hours:.1f} Hours**")

    if not vehicles:
        st.info("No vehicles currently available matching the exact criteria. Try adjusting the category or passenger count.")
        return

    # Render rental vehicles
    for v in vehicles:
        v_type = v.get("vehicle_type", "Hatchback")
        hourly_rate = SELF_DRIVE_HOURLY_RATES.get(v_type, 70.0)
        total_rent = duration_hours * hourly_rate

        pricing_info = v.get("pricing_details", {})
        deposit = pricing_info.get("security_deposit", 1500)
        fuel = pricing_info.get("fuel_type", "Petrol")

        with st.container():
            col_r1, col_r2, col_r3 = st.columns([2.5, 1.2, 1.3])

            with col_r1:
                st.markdown(f"""
                <div style="font-size:1.1rem; font-weight:700; color:#0F172A;">{v.get('vehicle_model')}</div>
                <div style="font-size:0.85rem; color:#64748B; margin-top:2px;">
                    💺 {v.get('seating_capacity')} Seats • ⛽ {fuel} • Deposit: {format_inr(deposit)} • Agency: <strong>{v.get('business_name')}</strong>
                </div>
                """, unsafe_allow_html=True)

            with col_r2:
                st.markdown(f"""
                <div style="text-align:right;">
                    <div style="font-size:1.25rem; font-weight:800; color:#0F172A;">{format_inr(total_rent)}</div>
                    <div style="font-size:0.75rem; color:#64748B;">{format_inr(hourly_rate)}/hr • {duration_hours:.0f} hrs</div>
                </div>
                """, unsafe_allow_html=True)

            with col_r3:
                if st.button("Book Rental", key=f"book_sd_{v['id']}", use_container_width=True, type="primary"):
                    try:
                        AnalyticsService.log_event("booking_started", user_id=student["id"], metadata={"vehicle_id": v["id"], "fare": total_rent, "segment": "Self-Drive"})
                    except Exception:
                        pass
                    trip_ctx = {
                        "pickup": "GIM Gate No. 2",
                        "dropoff": "Self-Drive Return (Gate 2)",
                        "base_trip_fare": total_rent,
                        "passengers": pax_count,
                        "duration": f"{duration_hours:.1f} hours",
                        "start_dt": start_dt.isoformat(),
                        "end_dt": end_dt.isoformat()
                    }
                    show_booking_confirmation_dialog(v, student, trip_ctx)

            st.divider()


@st.dialog("💳 Payment & Booking Confirmation", width="large")
def show_booking_confirmation_dialog(vehicle: Dict[str, Any], student: Dict[str, Any], trip_context: Dict[str, Any]):
    """Native popup confirmation dialog."""
    pickup_point = trip_context.get("pickup", "GIM Gate No. 2")
    destination = trip_context.get("dropoff", "Goa Destination")
    base_fare = float(trip_context.get("base_trip_fare", 0.0))
    total_due = base_fare + PLATFORM_CONVENIENCE_FEE
    duration_str = trip_context.get("duration", "1.5 hours")
    passengers = trip_context.get("passengers", 1)

    st.markdown(f"""
    <div style="background:#F8FAFC; border:1px solid #E2E8F0; border-radius:12px; padding:16px; margin-bottom:14px;">
        <div style="font-size:0.8rem; font-weight:700; color:#2563EB; text-transform:uppercase;">Trip Summary</div>
        <div style="font-size:1.15rem; font-weight:700; color:#0F172A; margin:4px 0;">📍 {pickup_point} ➔ {destination}</div>
        <div style="font-size:0.85rem; color:#475569;">
            Vehicle: <strong>{vehicle.get('vehicle_model')}</strong> ({vehicle.get('vehicle_number')})<br/>
            Provider: <strong>{vehicle.get('business_name')}</strong> • {passengers} Passenger(s) • {duration_str}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Billing breakdown
    st.markdown("##### 🧾 Transparent Billing Breakdown")
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        st.markdown(f"""
        • Trip Fare (100% to Driver):<br/>
        • Campus Platform Fee:<br/>
        <strong style="font-size:1.1rem; color:#0F172A;">Total Amount:</strong>
        """, unsafe_allow_html=True)
    with col_b2:
        st.markdown(f"""
        <div style="text-align:right;">
            <strong>{format_inr(base_fare)}</strong><br/>
            <strong>{format_inr(PLATFORM_CONVENIENCE_FEE)}</strong><br/>
            <strong style="font-size:1.1rem; color:#2563EB;">{format_inr(total_due)}</strong>
        </div>
        """, unsafe_allow_html=True)

    st.caption("🔒 0% Driver Commission: 100% of the trip fare goes directly to the verified local partner.")

    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

    if st.button("✅ Confirm Booking", use_container_width=True, type="primary"):
        with st.spinner("Confirming booking with provider..."):
            ok, msg, booking = BookingService.create_booking_request(
                student_id=student["id"],
                vehicle_id=vehicle["id"],
                provider_id=vehicle["provider_id"],
                service_segment=vehicle.get("service_segment", "Cab"),
                vehicle_category=vehicle.get("vehicle_category", "Cab"),
                vehicle_type=vehicle.get("vehicle_type", "Sedan"),
                pickup_location=pickup_point,
                dropoff_location=destination,
                start_datetime=trip_context.get("start_dt", datetime.datetime.now().isoformat()),
                end_datetime=trip_context.get("end_dt"),
                passengers_count=passengers,
                rental_duration=duration_str,
                base_trip_fare=base_fare,
                auto_pay_fee=True
            )
            if ok:
                st.session_state["booking_just_confirmed"] = True
                st.session_state["active_booking_id"] = booking["id"]
                st.balloons()
                st.rerun()
            else:
                st.toast(msg, icon="⚠️")
                st.error(f"Booking could not be completed: {msg}")


def render_active_bookings_section(student: Dict[str, Any], active_bookings: Optional[List[Dict[str, Any]]] = None):
    """Real-time active ride passes and trip tracking."""
    st.markdown("### 📍 Active Ride Passes & Tracking")
    if active_bookings is None:
        try:
            active_bookings = BookingService.get_active_bookings_for_student(student["id"])
        except Exception:
            active_bookings = []

    if not active_bookings:
        st.info("You currently have no active or in-progress trips. Book a ride from the 'Book a Ride' tab.")
        return

    for b in active_bookings:
        b_id = b["id"]
        status = b.get("booking_status", "confirmed")
        phone_unmasked = b.get("provider_phone") or b.get("driver_phone") or "+91 98221 55667"
        driver_name = b.get("driver_business") or b.get("business_name") or b.get("driver_name") or "Verified Campus Driver"

        status_tag = {
            "confirmed": ("Confirmed", "#D1FAE5", "#065F46"),
            "in_progress": ("On the Way", "#DBEAFE", "#1E40AF"),
            "requested": ("Pending Partner", "#FEF3C7", "#92400E")
        }.get(status, ("Active", "#F1F5F9", "#334155"))

        with st.container():
            st.markdown(f"""
            <div class="stCard">
                <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
                    <div>
                        <span style="background:{status_tag[1]}; color:{status_tag[2]}; padding:3px 10px; border-radius:9999px; font-weight:700; font-size:0.8rem;">
                            🟢 {status_tag[0]}
                        </span>
                        <h3 style="margin:8px 0 2px 0; font-size:1.2rem; color:#0F172A;">{b.get('pickup_location')} ➔ {b.get('dropoff_location')}</h3>
                        <span style="font-size:0.85rem; color:#64748B;">Pass ID: #{b_id[:8]} • Vehicle: <strong>{b.get('vehicle_model')}</strong> ({b.get('vehicle_number')})</span>
                    </div>
                    <div style="text-align:right;">
                        <div style="font-size:1.3rem; font-weight:800; color:#2563EB;">{format_inr(b.get('base_trip_fare', 0))}</div>
                        <span style="font-size:0.75rem; color:#059669; font-weight:600;">Fee Paid: ₹20</span>
                    </div>
                </div>
                <div style="background:#F8FAFC; border-radius:10px; padding:12px; margin-top:12px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
                    <div>
                        <span style="font-size:0.75rem; color:#64748B; text-transform:uppercase;">Driver Contact (Unmasked)</span>
                        <div style="font-size:1rem; font-weight:700; color:#0F172A;">📞 {phone_unmasked}</div>
                        <span style="font-size:0.8rem; color:#475569;">Driver: <strong>{driver_name}</strong></span>
                    </div>
                    <div>
                        <span style="font-size:0.75rem; color:#64748B; text-transform:uppercase;">Pickup Point</span>
                        <div style="font-size:0.95rem; font-weight:600; color:#0F172A;">GIM Gate No. 2</div>
                        <span style="font-size:0.8rem; color:#475569;">Rental / Trip Pass Active</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            col_a1, col_a2 = st.columns([1, 4])
            with col_a1:
                if st.button("Cancel Ride", key=f"cancel_{b_id}", use_container_width=True):
                    BookingService.update_booking_status(b_id, BookingStatus.CANCELLED.value)
                    st.toast("Ride cancelled successfully.", icon="ℹ️")
                    st.rerun()


def render_history_section(student: Dict[str, Any]):
    """Completed trip ledger and post-trip review desk."""
    st.markdown("### 📜 Past Trips & Reviews")
    try:
        bookings = BookingService.get_student_bookings(student["id"])
        past_bookings = [b for b in bookings if b.get("booking_status") in ("completed", "cancelled")]
    except Exception:
        past_bookings = []

    if not past_bookings:
        st.info("No past completed trips found.")
        return

    for pb in past_bookings:
        status = pb.get("booking_status", "completed")
        with st.container():
            col_h1, col_h2, col_h3 = st.columns([3, 1, 1])
            with col_h1:
                st.markdown(f"""
                <strong>{pb.get('pickup_location')} ➔ {pb.get('dropoff_location')}</strong><br/>
                <span style="font-size:0.8rem; color:#64748B;">{pb.get('vehicle_model')} • {pb.get('rental_duration_days_or_hours')}</span>
                """, unsafe_allow_html=True)
            with col_h2:
                st.markdown(f"**{format_inr(pb.get('base_trip_fare', 0))}**<br/><span style='font-size:0.75rem; color:#64748B;'>{status.title()}</span>", unsafe_allow_html=True)
            with col_h3:
                st.caption(f"Trip #{pb['id'][:6]}")
            st.divider()


def render_grievance_section(student: Dict[str, Any]):
    """Grievance and dispute desk for students."""
    st.markdown("### 💬 Campus Help & Dispute Desk")
    st.caption("File any incident, overcharging, or route issue directly with the GIM Transport Committee.")

    # Retrieve student's trips for selection
    try:
        student_trips = BookingService.get_student_bookings(student["id"])
    except Exception:
        student_trips = []

    trip_options = {"General Campus Feedback / Non-Trip Issue": None}
    for b in student_trips:
        label = f"Trip #{b['id'][:8]} — {b.get('dropoff_location')} ({b.get('vehicle_model')})"
        trip_options[label] = b["id"]

    with st.form("student_complaint_form", clear_on_submit=True):
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            comp_type = st.selectbox(
                "Category",
                [ComplaintType.OVERCHARGING.value, ComplaintType.DRIVER_BEHAVIOR.value, ComplaintType.VEHICLE_CONDITION.value, ComplaintType.CANCELLATION.value, ComplaintType.SAFETY.value, ComplaintType.OTHER.value],
                format_func=lambda x: x.replace("_", " ").title()
            )
        with col_c2:
            chosen_trip_label = st.selectbox("Related Trip (Optional)", list(trip_options.keys()))

        comp_desc = st.text_area("Describe the Issue", placeholder="Provide clear details regarding the driver behavior, route dispute, or vehicle condition...")

        submit_ticket = st.form_submit_button("Submit Ticket to Transport Admin", type="primary", use_container_width=True)

        if submit_ticket:
            if not comp_desc.strip():
                st.toast("Please describe the issue in detail.", icon="⚠️")
            else:
                chosen_b_id = trip_options.get(chosen_trip_label)
                ok, msg, comp_rec = ComplaintService.file_complaint(
                    raised_by_id=student["id"],
                    complaint_type=comp_type,
                    description=comp_desc.strip(),
                    booking_id=chosen_b_id
                )
                if ok:
                    st.toast("Ticket raised successfully! Transport committee has been notified.", icon="✅")
                    st.success("Your ticket has been logged and assigned to campus administration.")
                else:
                    st.toast(msg, icon="⚠️")
                    st.error(msg)

    st.markdown("---")
    st.markdown("#### 📋 Your Submitted Tickets")

    try:
        user_complaints = ComplaintService.get_student_complaints(student["id"])
    except Exception:
        user_complaints = []

    if not user_complaints:
        st.info("You have not raised any active grievance tickets.")
        return

    for c in user_complaints:
        c_status = c.get("status", "open")
        status_tag = {
            "open": ("🟡 Open", "#FEF3C7", "#92400E"),
            "under_investigation": ("🔵 In Review", "#DBEAFE", "#1E40AF"),
            "resolved": ("🟢 Resolved", "#D1FAE5", "#065F46"),
            "dismissed": ("⚪ Closed", "#F1F5F9", "#475569")
        }.get(c_status, ("🟡 Open", "#FEF3C7", "#92400E"))

        with st.container(border=True):
            col_t1, col_t2 = st.columns([3.5, 1.5])
            with col_t1:
                st.markdown(
                    f"<span style='background:{status_tag[1]}; color:{status_tag[2]}; padding:3px 10px; border-radius:9999px; font-weight:700; font-size:0.78rem; display:inline-block; margin-bottom:6px;'>"
                    f"{status_tag[0]}</span> <strong style='font-size:1.05rem; color:#0F172A; margin-left:6px;'>"
                    f"{c.get('complaint_type', '').replace('_', ' ').title()}</strong>",
                    unsafe_allow_html=True
                )
                st.markdown(
                    f"<div style='color:#334155; font-size:0.92rem; margin:6px 0; line-height:1.4;'>"
                    f"{c.get('description')}</div>",
                    unsafe_allow_html=True
                )
                if c.get("admin_notes"):
                    st.success(f"**Campus Admin Note:** {c.get('admin_notes')}")
            with col_t2:
                created = c.get("created_at", "")[:10]
                st.markdown(
                    f"<div style='text-align:right; font-size:0.75rem; color:#94A3B8;'>"
                    f"Ticket #{c.get('id', '')[:8]}<br/>{created}</div>",
                    unsafe_allow_html=True
                )
