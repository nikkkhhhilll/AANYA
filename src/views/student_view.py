"""
Student Portal View for GIM Campus Mobility.
100% Mobile-First / Mobile-Only optimized layout (Uber/Airbnb style).
Features compact mobile hero, equal-width tab buttons, native mobile transit pass, and touch-friendly cards.
"""
import datetime
import streamlit as st
import pandas as pd
from typing import Dict, Any, List, Optional
from src.config import (
    ServiceSegment, VehicleCategory, VehicleType, BookingStatus,
    ComplaintType, PLATFORM_CONVENIENCE_FEE, format_inr
)
from src.services.pricing_service import PricingService
from src.services.vehicle_service import VehicleService
from src.services.booking_service import BookingService
from src.services.complaint_service import ComplaintService
from src.services.analytics_service import AnalyticsService
from src.services.distance_service import DistanceService


def render_student_portal(student: Dict[str, Any]):
    """Render 100% mobile-first student mobility interface."""
    student_id = student.get("id")
    student_name = student.get("full_name", "Student")
    student_program = student.get("program", "PGDM")
    # Inject helper JS (Clipboard Copy & Card Click Listeners)
    st.markdown("""
    <div id="gim-toast" class="custom-toast">Copied to clipboard!</div>
    
    <script>
    (function() {
        // Clipboard Copy function
        window.gimCopyText = function(text, btnElement) {
            navigator.clipboard.writeText(text).then(() => {
                const toast = document.getElementById('gim-toast');
                if (toast) {
                    toast.classList.add('show');
                    setTimeout(() => { toast.classList.remove('show'); }, 2000);
                }
                const iconSpan = btnElement.querySelector('.copy-icon');
                if (iconSpan) {
                    const original = iconSpan.innerHTML;
                    iconSpan.innerHTML = '✅';
                    setTimeout(() => { iconSpan.innerHTML = original; }, 1500);
                }
            });
        };
        
        // Active Card click listener helper
        function attachCardListeners() {
            const cardInners = document.querySelectorAll('.gim-vehicle-card-inner');
            cardInners.forEach(inner => {
                const wrapper = inner.closest('div[data-testid="element-container"]').parentNode;
                if (!wrapper) return;
                
                // Add styling class
                wrapper.classList.add('gim-vehicle-card');
                
                if (wrapper.dataset.listenerAttached) return;
                wrapper.dataset.listenerAttached = 'true';
                
                wrapper.addEventListener('click', function(e) {
                    if (e.target.tagName === 'BUTTON' || e.target.closest('button')) return;
                    const selectBtn = wrapper.querySelector('button');
                    if (selectBtn) {
                        selectBtn.click();
                    }
                });
            });
        }
        
        setInterval(attachCardListeners, 500);
    })();
    </script>
    """, unsafe_allow_html=True)

    # Compact Mobile Hero Header
    st.markdown(f"""
    <div class="gim-hero">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
                <div style="font-size:1.35rem; font-weight:800; color:#FFFFFF; letter-spacing:-0.02em;">Ride Smart</div>
                <div style="font-size:0.85rem; color:#DBEAFE; margin-top:2px;">{student_name} • {student_program}</div>
            </div>
            <span style="font-size:0.75rem; background:rgba(255,255,255,0.22); padding:4px 10px; border-radius:9999px; color:#FFFFFF; font-weight:600;">
                ✓ Verified
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Toast notification if booking was just made
    if st.session_state.get("booking_just_confirmed"):
        st.toast("🎉 Booking confirmed! Pass is now active.", icon="✅")
        st.session_state["booking_just_confirmed"] = False

    # Log page view telemetry once per session
    if not st.session_state.get("page_view_logged"):
        try:
            AnalyticsService.log_event("page_view", user_id=student_id, metadata={"portal": "student_view"})
            st.session_state["page_view_logged"] = True
        except Exception:
            pass

    # Fetch active bookings for dynamic tab counter & top banner
    try:
        active_bookings = BookingService.get_active_bookings_for_student(student_id)
    except Exception:
        active_bookings = []

    # Active Trip Notification Banner (Mobile Pass Card)
    if active_bookings:
        latest = active_bookings[0]
        latest_phone = latest.get("provider_phone") or latest.get("driver_phone") or "+91 94220 66778"
        latest_driver = latest.get("business_name") or latest.get("driver_name") or "Verified Driver"
        st.markdown(f"""
        <div style="background: var(--bg-surface); border: 1.5px solid var(--border-subtle); border-radius: 14px; padding: 14px 16px; margin-bottom: 14px; box-shadow: var(--shadow-md);">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="background: var(--status-success-bg); color: var(--status-success-text); font-weight: 700; font-size: 0.72rem; padding: 2px 8px; border-radius: 9999px; text-transform: uppercase;">
                    🟢 Active Booking
                </span>
                <span style="font-size: 1.15rem; font-weight: 800; color: #10B981;">{format_inr(latest.get('base_trip_fare', 0))}</span>
            </div>
            <div style="font-size: 1.05rem; font-weight: 700; color: var(--text-primary); margin: 8px 0 4px 0;">
                📍 {latest.get('pickup_location')} ➔ {latest.get('dropoff_location')}
            </div>
            <div style="font-size: 0.82rem; color: var(--text-secondary); line-height: 1.4;">
                Driver: <strong>{latest_driver}</strong><br/>
                Vehicle: <strong>{latest.get('vehicle_model')}</strong> ({latest.get('vehicle_number')})
            </div>
            <div style="margin-top: 10px; display: flex; justify-content: space-between; align-items: center; flex-wrap:wrap; gap:8px;">
                <a href="tel:{latest_phone.replace(' ', '')}" style="display: inline-block; background: #2563EB; color: #FFFFFF; font-size: 0.8rem; font-weight: 700; padding: 6px 12px; border-radius: 8px; text-decoration: none;">
                    📞 Call Driver ({latest_phone})
                </a>
                <span style="font-size: 0.72rem; color: var(--status-success-text); font-weight: 600;">✓ Gate 2 Pickup</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Mobile Compact Equal-Width Navigation Tabs
    tab_book, tab_trips, tab_help = st.tabs([
        "🚗 Book",
        "📍 Trips",
        "💬 Support"
    ])

    with tab_book:
        render_booking_section(student)

    with tab_trips:
        render_trips_section(student, active_bookings)

    with tab_help:
        render_grievance_section(student)


def render_booking_section(student: Dict[str, Any]):
    """Dynamic ride & rental search with mobile-first segmented controls."""
    service_tabs = st.tabs(["🚖 Campus Cabs", "🚗 Self-Drive"])

    with service_tabs[0]:
        render_cab_booking_flow(student)

    with service_tabs[1]:
        render_self_drive_booking_flow(student)


def render_cab_booking_flow(student: Dict[str, Any]):
    """Mobile-first cab booking interface with clean route calculations."""
    pickup_loc = "GIM Gate No. 2"

    st.markdown("""
    <div style="font-size:0.8rem; color:var(--brand-accent); font-weight:600; margin-bottom:10px;">
        📍 <strong>Pickup Point:</strong> GIM Gate No. 2 (All verified campus cabs).
    </div>
    """, unsafe_allow_html=True)

    destination_list = DistanceService.get_all_destination_names()
    route_options = destination_list

    selected_dest = st.selectbox("Where to?", route_options, index=min(3, len(route_options)-1), key="cab_dest_sel")
    final_dest = selected_dest

    # Log segment selection once
    if st.session_state.get("last_segment") != "Cab":
        try:
            AnalyticsService.log_event("segment_selected", user_id=student["id"], metadata={"segment": "Cab"})
            st.session_state["last_segment"] = "Cab"
        except Exception:
            pass

    # Log search query when destination changes
    if final_dest and st.session_state.get("last_cab_dest") != final_dest:
        try:
            AnalyticsService.log_event("search_query", user_id=student["id"], metadata={"origin": pickup_loc, "destination": final_dest})
            st.session_state["last_cab_dest"] = final_dest
        except Exception:
            pass

    passengers_count = st.selectbox(
        "Passengers",
        [1, 2, 3, 4, 5, 6],
        index=0,
        key="cab_pax_count"
    )

    # Route Distance Calculation
    try:
        calc_dest = selected_dest if selected_dest != "Custom Destination / Other" else "Panjim (Panaji)"
        distance_km, duration_mins, route_desc = DistanceService.get_route_distance("GIM Campus, Sanquelim", calc_dest)
    except Exception:
        distance_km, duration_mins = 31.0, 45

    # Compact Mobile Route Summary Bar
    st.markdown(f"""
    <div class="route-badge-bar">
        <span>📍 <strong>Gate 2</strong> ➔ <strong>{final_dest}</strong></span>
        <span style="color:var(--brand-accent); font-weight:700;">{distance_km:.1f} km • ~{duration_mins} mins</span>
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

    st.markdown(f"**Available Verified Cabs ({len(available_cabs)}):**")

    # Mobile-First Vehicle Cards (Vertical touch-friendly layout)
    for cab in available_cabs:
        tier = cab.get("vehicle_type", "Sedan")
        if tier not in ["Hatchback", "Sedan", "SUV"]:
            tier = "Sedan"

        fare_calc = DistanceService.calculate_fare(distance_km, tier)
        trip_fare = fare_calc["total_fare"]
        rate_km = fare_calc["rate_per_km"]

        total_seats = int(cab.get("seating_capacity", 4))
        pax_capacity = max(1, total_seats - 1)

        tier_tag = {
            "Hatchback": ("Eco", "#D1FAE5", "#065F46"),
            "Sedan": ("Comfort", "#EFF6FF", "#1D4ED8"),
            "SUV": ("XL", "#FEF3C7", "#92400E")
        }.get(tier, ("Standard", "#F1F5F9", "#475569"))

        with st.container(border=True):
            # Card Top Row: Vehicle name & Price
            st.markdown(f"""
            <div class="gim-vehicle-card-inner" id="cab_card_inner_{cab['id']}">
                <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                    <div>
                        <div style="font-size:1.1rem; font-weight:700; color:var(--text-primary);">{cab.get('vehicle_model')}</div>
                        <span style="background:{tier_tag[1]}; color:{tier_tag[2]}; padding:2px 8px; border-radius:9999px; font-size:0.75rem; font-weight:600;">{tier_tag[0]}</span>
                        <span style="font-size:0.8rem; color:var(--text-secondary); margin-left:4px;">💺 {pax_capacity} Seats</span>
                    </div>
                    <div style="text-align:right;">
                        <div style="font-size:1.25rem; font-weight:800; color:var(--text-primary);">{format_inr(trip_fare)}</div>
                        <div style="font-size:0.72rem; color:var(--text-secondary);">₹{rate_km:.0f}/km • 0% cut</div>
                    </div>
                </div>
                <div style="font-size:0.82rem; color:var(--text-secondary); margin:6px 0 0 0;">
                    Driver: <strong>{cab.get('business_name')}</strong> • ⭐ {cab.get('driver_rating', 5.0):.1f} ({cab.get('total_trips', 0)} trips)
                </div>
            </div>
            """, unsafe_allow_html=True)

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


def render_self_drive_booking_flow(student: Dict[str, Any]):
    """Mobile-first self-drive car and bike rentals."""
    st.caption("Drive yourself across Goa with transparent hourly rates.")

    col_c1, col_c2, col_c3 = st.columns(3)

    with col_c1:
        chosen_cat = st.selectbox(
            "1. Vehicle Category",
            [VehicleCategory.FOUR_WHEELER.value, VehicleCategory.TWO_WHEELER.value],
            format_func=lambda x: "🚗 4-Wheeler (Cars)" if x == VehicleCategory.FOUR_WHEELER.value else "🛵 2-Wheeler (Bikes & Scooties)",
            key="sd_cat_sel"
        )

    # Log segment selection once
    if st.session_state.get("last_segment") != "Self-Drive":
        try:
            AnalyticsService.log_event("segment_selected", user_id=student["id"], metadata={"segment": "Self-Drive"})
            st.session_state["last_segment"] = "Self-Drive"
        except Exception:
            pass

    # Log search query when category changes
    if chosen_cat and st.session_state.get("last_sd_cat") != chosen_cat:
        try:
            AnalyticsService.log_event("search_query", user_id=student["id"], metadata={"origin": "GIM Gate No. 2", "category": chosen_cat})
            st.session_state["last_sd_cat"] = chosen_cat
        except Exception:
            pass

    if chosen_cat == VehicleCategory.FOUR_WHEELER.value:
        type_options = ["All", VehicleType.HATCHBACK.value, VehicleType.SEDAN.value, VehicleType.SUV.value]
    else:
        type_options = ["All", VehicleType.SCOOTY.value, VehicleType.BIKE.value]

    with col_c2:
        chosen_type = st.selectbox("2. Vehicle Type", type_options, key="sd_type_sel")

    if chosen_cat == VehicleCategory.TWO_WHEELER.value:
        pax_options = [1, 2]
    elif chosen_type == VehicleType.SUV.value:
        pax_options = [1, 2, 3, 4, 5, 6, 7]
    else:
        pax_options = [1, 2, 3, 4, 5]

    with col_c3:
        pax_count = st.selectbox(
            "3. Passengers Count",
            pax_options,
            index=0,
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
        st.warning("⚠️ Return time must be after pickup time.")
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

    st.markdown(f"**Available Fleet ({len(vehicles)}) • Duration: {duration_hours:.1f} hrs:**")

    if not vehicles:
        st.info("No vehicles currently available matching the exact criteria.")
        return

    for v in vehicles:
        v_type = v.get("vehicle_type", "Hatchback")
        self_drive_rates = PricingService.get_self_drive_hourly_rates()
        hourly_rate = self_drive_rates.get(v_type, 70.0)
        total_rent = duration_hours * hourly_rate

        pricing_info = v.get("pricing_details", {})
        deposit = pricing_info.get("security_deposit", 1500)
        fuel = pricing_info.get("fuel_type", "Petrol")

        with st.container(border=True):
            st.markdown(f"""
            <div class="gim-vehicle-card-inner" id="sd_card_inner_{v['id']}">
                <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                    <div>
                        <div style="font-size:1.1rem; font-weight:700; color:var(--text-primary);">{v.get('vehicle_model')}</div>
                        <span style="font-size:0.8rem; color:var(--text-secondary);">💺 {v.get('seating_capacity')} Seats • ⛽ {fuel}</span>
                    </div>
                    <div style="text-align:right;">
                        <div style="font-size:1.25rem; font-weight:800; color:var(--text-primary);">{format_inr(total_rent)}</div>
                        <div style="font-size:0.72rem; color:var(--text-secondary);">{format_inr(hourly_rate)}/hr</div>
                    </div>
                </div>
                <div style="font-size:0.82rem; color:var(--text-secondary); margin:6px 0 0 0;">
                    Deposit: {format_inr(deposit)} • Agency: <strong>{v.get('business_name')}</strong>
                </div>
            </div>
            """, unsafe_allow_html=True)

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


@st.dialog("💳 Confirm Booking", width="small")
def show_booking_confirmation_dialog(vehicle: Dict[str, Any], student: Dict[str, Any], trip_context: Dict[str, Any]):
    """Mobile popup confirmation dialog."""
    pickup_point = trip_context.get("pickup", "GIM Gate No. 2")
    destination = trip_context.get("dropoff", "Goa Destination")
    base_fare = float(trip_context.get("base_trip_fare", 0.0))
    total_due = base_fare + PLATFORM_CONVENIENCE_FEE
    duration_str = trip_context.get("duration", "1.5 hours")
    passengers = trip_context.get("passengers", 1)

    st.markdown(f"""
    <div style="background:var(--bg-main); border:1px solid var(--border-subtle); border-radius:10px; padding:12px; margin-bottom:12px;">
        <div style="font-size:0.75rem; font-weight:700; color:var(--brand-accent); text-transform:uppercase;">Trip Summary</div>
        <div style="font-size:1.05rem; font-weight:700; color:var(--text-primary); margin:3px 0;">📍 {pickup_point} ➔ {destination}</div>
        <div style="font-size:0.8rem; color:var(--text-secondary);">
            {vehicle.get('vehicle_model')} • {vehicle.get('business_name')}<br/>
            {passengers} Rider(s) • {duration_str}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Billing breakdown
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        st.markdown(f"""
        <div style="font-size:0.85rem; color:var(--text-secondary); line-height:1.6;">
            • Trip Fare (100% to Driver):<br/>
            • Platform Fee:<br/>
            <strong style="color:var(--text-primary); font-size:0.95rem;">Total:</strong>
        </div>
        """, unsafe_allow_html=True)
    with col_b2:
        st.markdown(f"""
        <div style="text-align:right; font-size:0.85rem; line-height:1.6;">
            <strong>{format_inr(base_fare)}</strong><br/>
            <strong>{format_inr(PLATFORM_CONVENIENCE_FEE)}</strong><br/>
            <strong style="color:var(--brand-accent); font-size:1.05rem;">{format_inr(total_due)}</strong>
        </div>
        """, unsafe_allow_html=True)

    st.caption("🔒 0% Driver Commission: 100% fare goes to verified local partner.")
    st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)


    if st.button("✅ Confirm Booking", use_container_width=True, type="primary"):
        with st.spinner("Confirming..."):
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
                st.error(msg)


def render_trips_section(student: Dict[str, Any], active_bookings: Optional[List[Dict[str, Any]]] = None):
    """Combined Trips panel showing Upcoming and Past trips."""
    
    # 📆 Upcoming Trip/s
    st.markdown("### 📆 Upcoming Trip/s")
    if active_bookings is None:
        try:
            active_bookings = BookingService.get_active_bookings_for_student(student["id"])
        except Exception:
            active_bookings = []

    if not active_bookings:
        st.info("No upcoming trips scheduled.")
    else:
        for b in active_bookings:
            b_id = b["id"]
            status = b.get("booking_status", "confirmed")
            phone_unmasked = b.get("provider_phone") or b.get("driver_phone") or "+91 94220 66778"
            driver_name = b.get("driver_business") or b.get("business_name") or b.get("driver_name") or "Verified Driver"

            with st.container(border=True):
                st.markdown(f"""
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 8px;">
                    <span style="background:#D1FAE5; color:#065F46; padding:2px 8px; border-radius:9999px; font-weight:700; font-size:0.75rem; text-transform:lowercase;">
                        🟢 confirmed
                    </span>
                    <span style="font-size:1.15rem; font-weight:800; color:var(--brand-accent);">{format_inr(b.get('base_trip_fare', 0))}</span>
                </div>
                
                <div style="margin-bottom: 8px;">
                    <span style="font-size:0.78rem; color:var(--text-secondary);">Pass Code:</span>
                    <span class="copyable-id" onclick="window.gimCopyText('{b_id[:6].upper()}', this)">#{b_id[:6].upper()} <span class="copy-icon">📋</span></span>
                </div>
                
                <div style="font-size:1.05rem; font-weight:700; color:var(--text-primary); margin:6px 0 2px 0;">
                    📍 {b.get('pickup_location')} ➔ {b.get('dropoff_location')}
                </div>
                
                <div style="font-size:0.82rem; color:var(--text-secondary); line-height:1.4;">
                    Driver: <strong>{driver_name}</strong><br/>
                    Vehicle: <strong>{b.get('vehicle_model')}</strong> ({b.get('vehicle_number')})
                </div>
                
                <div style="margin-top:10px; display:flex; gap:10px; align-items:center; flex-wrap:wrap;">
                    <a href="tel:{phone_unmasked.replace(' ', '')}" style="display:inline-block; background:var(--brand-accent); color:#FFFFFF; font-size:0.8rem; font-weight:700; padding:6px 12px; border-radius:8px; text-decoration:none;">
                        📞 Call Driver
                    </a>
                    <span class="copyable-id" onclick="window.gimCopyText('{phone_unmasked}', this)" style="padding:5px 10px; font-size:0.78rem;">
                        {phone_unmasked} <span class="copy-icon">📋</span>
                    </span>
                </div>
                """, unsafe_allow_html=True)

                if st.button("Cancel Booking", key=f"cancel_{b_id}", use_container_width=True):
                    BookingService.update_booking_status(b_id, BookingStatus.CANCELLED.value)
                    st.toast("Ride cancelled successfully.", icon="ℹ️")
                    st.rerun()

    st.markdown("---")

    # 📜 Past Trip/s
    st.markdown("### 📜 Past Trip/s")
    try:
        bookings = BookingService.get_student_bookings(student["id"])
        past_bookings = [b for b in bookings if b.get("booking_status") in ("completed", "cancelled")]
    except Exception:
        past_bookings = []

    if not past_bookings:
        st.info("No past trips found.")
    else:
        for pb in past_bookings:
            status = pb.get("booking_status", "completed")
            with st.container(border=True):
                col_h1, col_h2 = st.columns([3, 1])
                with col_h1:
                    st.markdown(f"""
                    <strong style="color:var(--text-primary); font-size:0.95rem;">{pb.get('pickup_location')} ➔ {pb.get('dropoff_location')}</strong><br/>
                    <span style="font-size:0.8rem; color:var(--text-secondary);">{pb.get('vehicle_model')} • {pb.get('rental_duration') or '1.0 hours'}</span>
                    """, unsafe_allow_html=True)
                with col_h2:
                    badge_style = "background:#D1FAE5; color:#065F46;" if status == "completed" else "background:#F3F4F6; color:#374151;"
                    st.markdown(f"<div style='text-align:right;'><strong>{format_inr(pb.get('base_trip_fare', 0))}</strong><br/><span style='{badge_style} padding:2px 6px; border-radius:4px; font-size:0.72rem; font-weight:700;'>{status.title()}</span></div>", unsafe_allow_html=True)


def render_grievance_section(student: Dict[str, Any]):
    """Mobile dispute and grievance desk."""
    st.markdown("### 💬 Help & Dispute Desk")
    st.caption("File any incident or overcharging issue directly with the Campus Transport Committee.")

    try:
        student_trips = BookingService.get_student_bookings(student["id"])
    except Exception:
        student_trips = []

    trip_options = {"General Campus Feedback / Non-Trip Issue": None}
    for b in student_trips:
        label = f"Trip #{b['id'][:6]} — {b.get('dropoff_location')}"
        trip_options[label] = b["id"]

    with st.form("student_complaint_form", clear_on_submit=True):
        comp_type = st.selectbox(
            "Category",
            [ComplaintType.OVERCHARGING.value, ComplaintType.DRIVER_BEHAVIOR.value, ComplaintType.VEHICLE_CONDITION.value, ComplaintType.CANCELLATION.value, ComplaintType.SAFETY.value, ComplaintType.OTHER.value],
            format_func=lambda x: x.replace("_", " ").title()
        )
        chosen_trip_label = st.selectbox("Related Trip (Optional)", list(trip_options.keys()))
        comp_desc = st.text_area("Describe the Issue", placeholder="Provide clear details regarding the driver behavior or trip dispute...")

        submit_ticket = st.form_submit_button("Submit Ticket", type="primary", use_container_width=True)

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
                    st.toast("Ticket raised successfully! Transport committee notified.", icon="✅")
                    st.success("Your ticket has been logged with campus administration.")
                else:
                    st.toast(msg, icon="⚠️")
                    st.error(msg)

    st.markdown("---")
    st.markdown("#### 📋 Submitted Tickets")

    try:
        user_complaints = ComplaintService.get_student_complaints(student["id"])
    except Exception:
        user_complaints = []

    if not user_complaints:
        st.info("No active grievance tickets.")
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
            col_t1, col_t2 = st.columns([3, 1])
            with col_t1:
                st.markdown(
                    f"<span style='background:{status_tag[1]}; color:{status_tag[2]}; padding:2px 8px; border-radius:9999px; font-weight:700; font-size:0.75rem;'>"
                    f"{status_tag[0]}</span> <strong style='font-size:0.95rem; color:var(--text-primary); margin-left:4px;'>"
                    f"{c.get('complaint_type', '').replace('_', ' ').title()}</strong></div>",
                    unsafe_allow_html=True
                )
                st.markdown(f"<div style='color:var(--text-secondary); font-size:0.88rem; margin:6px 0;'>{c.get('description')}</div>", unsafe_allow_html=True)
                if c.get("admin_notes"):
                    st.info(f"💡 Investigator: {c.get('admin_notes')}")
                st.markdown(f"<div style='text-align:right; font-size:0.72rem; color:var(--text-muted);'>{c.get('id', '')[:6]}</div>", unsafe_allow_html=True)
            with col_t2:
                st.markdown(f"<div style='text-align:right; font-size:0.72rem; color:var(--text-muted);'>#{c.get('id', '')[:6]}</div>", unsafe_allow_html=True)
