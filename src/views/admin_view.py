"""
Administrative Command Console for GIM Campus Mobility.
Light theme (Uber/Airbnb style) with high-contrast typography, driver KYC reviews, dispute resolution, student directory, ratings leaderboard, and analytics.
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import Dict, Any, List
from src.config import Role, BookingStatus, ComplaintStatus, format_inr
from src.services.auth_service import AuthService
from src.services.vehicle_service import VehicleService
from src.services.booking_service import BookingService
from src.services.complaint_service import ComplaintService
from src.services.analytics_service import AnalyticsService
from src.services.pricing_service import PricingService


def render_admin_portal(admin_user: Dict[str, Any]):
    """Render main transport committee administration view."""
    admin_name = admin_user.get("full_name", "Transport Admin")
    admin_email = admin_user.get("email", "")

    # Admin Hero Header
    st.markdown(f"""
    <div class="gim-hero">
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
            <div>
                <h2 style="margin:0; font-size:1.8rem; font-weight:800; color:#FFFFFF;">Campus Transport Command Center</h2>
                <p style="margin:4px 0 0 0; font-size:0.95rem; color:#DBEAFE;">
                    Signed in as <strong>{admin_name}</strong> • Campus Mobility Oversight
                </p>
            </div>
            <div style="background:rgba(255,255,255,0.18); border-radius:12px; padding:6px 14px; border:1px solid rgba(255,255,255,0.3);">
                <span style="font-size:0.75rem; color:#DBEAFE; text-transform:uppercase; letter-spacing:0.04em;">Official Role</span><br/>
                <span style="font-size:0.9rem; color:#FFFFFF; font-weight:600;">🛡️ Transport Administrator</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 7 Management Tabs
    tab_students, tab_drivers, tab_bookings, tab_complaints, tab_ratings, tab_analytics, tab_pricing = st.tabs([
        "👥 Manage Students",
        "🚗 Manage Drivers & KYC",
        "📋 Manage Bookings",
        "⚖️ Manage Complaints",
        "⭐ Ratings & Leaderboard",
        "📊 Interactive Analytics",
        "💰 Pricing & Fare Settings"
    ])

    with tab_students:
        render_manage_students()

    with tab_drivers:
        render_manage_drivers()

    with tab_bookings:
        render_manage_bookings()

    with tab_complaints:
        render_manage_complaints()

    with tab_ratings:
        render_manage_ratings()

    with tab_analytics:
        render_analytics_dashboard()

    with tab_pricing:
        render_manage_pricing()


# ============================================================================
# TAB 1: MANAGE STUDENTS
# ============================================================================
def render_manage_students():
    st.markdown("### 👥 Student Directory & Domain Access Control")
    students = AuthService.get_students()

    # Summary metrics
    total_students = len(students)
    active_students = len([s for s in students if s.get("is_active")])

    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        st.metric("Total Registered Students", total_students)
    with col2:
        st.metric("Active Campus Accounts", active_students)
    with col3:
        st.metric("Domain Enforced", "@gim.ac.in (100%)")

    # Search & Filter
    search_q = st.text_input("🔍 Search by Student Name, Email, or Program", placeholder="E.g. Priya, BDA, aravind.k24@gim.ac.in", key="search_students")

    filtered = students
    if search_q:
        q = search_q.lower()
        filtered = [s for s in students if q in s.get("full_name", "").lower() or q in s.get("email", "").lower() or q in s.get("program", "").lower()]

    st.markdown(f"#### Registered Students ({len(filtered)})")
    for s in filtered:
        s_id = s.get("id")
        is_active = bool(s.get("is_active", 1))
        
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([2.5, 2.5, 1.5, 1.5])
            with c1:
                st.markdown(f"<strong style='font-size:1.05rem; color:#0F172A;'>{s.get('full_name')}</strong>", unsafe_allow_html=True)
                st.caption(f"ID: `{s_id[:8]}` • Joined: {s.get('created_at', '')[:10]}")
            with c2:
                st.markdown(f"📧 `{s.get('email')}`")
                st.caption(f"📞 {s.get('phone')}")
            with c3:
                st.markdown(f"<span style='background:#EFF6FF; color:#1D4ED8; padding:3px 8px; border-radius:6px; font-weight:600; font-size:0.8rem;'>{s.get('program') or 'PGDM'}</span>", unsafe_allow_html=True)
            with c4:
                status_toggle = st.toggle("Active", value=is_active, key=f"std_active_{s_id}")
                if status_toggle != is_active:
                    AuthService.update_user_status(s_id, status_toggle)
                    st.toast(f"Student account status updated.")
                    st.rerun()


# ============================================================================
# TAB 2: MANAGE DRIVERS & PROVIDERS
# ============================================================================
def render_manage_drivers():
    st.markdown("### 🚗 Driver & Rental Provider KYC Verification Desk")
    drivers = VehicleService.get_all_drivers_kyc()

    # KYC Metrics
    total_d = len(drivers)
    verified_d = len([d for d in drivers if d.get("is_verified")])
    pending_d = total_d - verified_d

    c1, c2, c3 = st.columns(3)
    c1.metric("Registered Vendors", total_d)
    c2.metric("KYC Verified Partners", verified_d)
    c3.metric("Pending Verification", pending_d, delta=-pending_d if pending_d > 0 else 0)

    st.markdown("#### KYC Documents & Verification Queue")
    for d in drivers:
        d_id = d.get("id")
        is_verified = bool(d.get("is_verified", False))
        rating = float(d.get("rating", 5.0))
        trips = int(d.get("total_completed_trips", 0))

        with st.container(border=True):
            col1, col2, col3 = st.columns([3, 2, 2])
            with col1:
                st.markdown(f"<strong style='font-size:1.05rem; color:#0F172A;'>{d.get('business_name') or d.get('full_name')}</strong> ({d.get('full_name')})", unsafe_allow_html=True)
                st.caption(f"License: `{d.get('license_number')}` | Phone: `{d.get('phone')}` | Email: `{d.get('email')}`")
                if d.get("id_proof_url"):
                    st.markdown(f"[📄 View Submitted KYC Document]({d.get('id_proof_url')})")
            with col2:
                st.markdown(f"⭐ Rating: **{rating:.1f}/5.0** ({trips} trips)")
                if rating < 3.5:
                    st.warning("⚠️ Low Rating Alert (< 3.5)")
            with col3:
                verify_toggle = st.toggle("KYC Approved", value=is_verified, key=f"kyc_v_{d_id}")
                if verify_toggle != is_verified:
                    VehicleService.update_provider_verification(d_id, verify_toggle)
                    st.toast(f"Vendor verification updated to: {'Verified' if verify_toggle else 'Unverified'}")
                    st.rerun()
    # ================= Global Fleet Inventory Control =================
    st.markdown("---")
    st.markdown("### 🚙 Global Fleet Inventory Control")
    st.caption("View, edit, or remove any vehicle registered on the GIM Mobility Platform.")
    
    try:
        all_vehicles = VehicleService.get_all_vehicles()
    except Exception:
        all_vehicles = []
        
    if not all_vehicles:
        st.info("No vehicles registered on the platform.")
    else:
        for v in all_vehicles:
            v_id = v["id"]
            owner = v.get("business_name") or v.get("provider_name") or "Local Partner"
            
            with st.container(border=True):
                col_v1, col_v2, col_v3 = st.columns([3, 1.5, 1.2])
                with col_v1:
                    st.markdown(f"""
                    <strong style="font-size:1.05rem; color:#0F172A;">{v.get('vehicle_model')}</strong> ({v.get('vehicle_number')})<br/>
                    <span style="font-size:0.8rem; color:#64748B;">Owner: {owner} | Segment: {v.get('service_segment')} | Category: {v.get('vehicle_category')} | Seats: {v.get('seating_capacity')}</span>
                    """, unsafe_allow_html=True)
                with col_v2:
                    if st.button("✏️ Edit Vehicle", key=f"adm_edit_v_{v_id}", use_container_width=True):
                        show_edit_vehicle_dialog(v)
                with col_v3:
                    if st.button("🗑️ Delete", key=f"adm_del_v_{v_id}", type="secondary", use_container_width=True):
                        if VehicleService.delete_vehicle(v_id):
                            st.toast("Vehicle deleted from system.")
                            st.rerun()
                        else:
                            st.error("Failed to delete vehicle.")


@st.dialog("✏️ Edit Vehicle Record", width="small")
def show_edit_vehicle_dialog(vehicle: Dict[str, Any]):
    st.markdown(f"**Vehicle ID:** `{vehicle['id'][:8].upper()}`")
    
    with st.form("edit_vehicle_form"):
        v_model = st.text_input("Vehicle Model", value=vehicle.get("vehicle_model", ""))
        v_number = st.text_input("Registration Number", value=vehicle.get("vehicle_number", ""))
        v_seats = st.number_input("Seating Capacity", min_value=1, max_value=8, value=int(vehicle.get("seating_capacity", 4)))
        
        segment = vehicle.get("service_segment", "Cab")
        category = vehicle.get("vehicle_category", "Cab")
        v_type = vehicle.get("vehicle_type", "Sedan")
        
        pricing = vehicle.get("pricing_details", {})
        if not isinstance(pricing, dict):
            pricing = {}

        if segment == "Self-Drive":
            sd_fuel = st.selectbox("Fuel Type", ["Petrol", "Diesel", "EV"], index=["Petrol", "Diesel", "EV"].index(pricing.get("fuel_type", "Petrol")))
            st.caption("💡 Pricing is locked. Fares are calculated dynamically from global settings.")
        else:
            st.caption("💡 Cab pricing is managed globally by administrative configuration.")

        save_changes = st.form_submit_button("Save Changes", type="primary", use_container_width=True)
        if save_changes:
            if not v_model.strip() or not v_number.strip():
                st.error("Please fill in all fields.")
            else:
                # Dynamically resolve current global pricing payload
                if segment == "Self-Drive":
                    sd_rates = PricingService.get_self_drive_hourly_rates()
                    rate = sd_rates.get(v_type, 70.0)
                    pricing_payload = {
                        "hourly_rate": rate,
                        "security_deposit": 1500.0,
                        "fuel_type": sd_fuel
                    }
                else:
                    cab_rules = PricingService.get_cab_fare_rules()
                    rule = cab_rules.get(v_type, cab_rules.get("Sedan", {"base_fare": 80.0, "rate_per_km": 22.0}))
                    pricing_payload = {
                        "base_fare": rule.get("base_fare", 80.0),
                        "rate_per_km": rule.get("rate_per_km", 22.0)
                    }

                ok = VehicleService.update_vehicle(
                    vehicle_id=vehicle["id"],
                    service_segment=segment,
                    vehicle_category=category,
                    vehicle_type=v_type,
                    vehicle_model=v_model,
                    vehicle_number=v_number,
                    seating_capacity=v_seats,
                    pricing_details=pricing_payload
                )
                if ok:
                    st.toast("Vehicle record updated successfully!", icon="🎉")
                    st.rerun()
                else:
                    st.error("Failed to update vehicle record.")


# ============================================================================
# TAB 3: MANAGE BOOKINGS
# ============================================================================
def render_manage_bookings():
    st.markdown("### 📋 Platform Master Booking Registry")
    bookings = BookingService.get_all_bookings()

    # Filter Controls
    col_f1, col_f2 = st.columns([1, 1])
    with col_f1:
        filter_status = st.selectbox("Filter by Status", ["All", "requested", "confirmed", "in_progress", "completed", "cancelled"], key="adm_b_status")
    with col_f2:
        filter_seg = st.selectbox("Filter by Segment", ["All", "Cab", "Self-Drive"], key="adm_b_seg")

    filtered = bookings
    if filter_status != "All":
        filtered = [b for b in filtered if b.get("booking_status") == filter_status]
    if filter_seg != "All":
        filtered = [b for b in filtered if b.get("service_segment") == filter_seg]

    st.markdown(f"**Showing {len(filtered)} Booking(s):**")

    for b in filtered:
        b_id = b.get("id")
        cur_status = b.get("booking_status", "requested")

        with st.expander(f"Booking #{b_id[:8]} • {b.get('vehicle_model')} • {cur_status.upper()} ({format_inr(b.get('base_trip_fare', 0))})"):
            col1, col2 = st.columns([1, 1])
            with col1:
                st.markdown(f"""
                - **Student:** {b.get('student_name')} (`{b.get('student_email')}`)
                - **Driver/Vendor:** {b.get('driver_business') or b.get('driver_name')} (`{b.get('driver_phone')}`)
                - **Route:** {b.get('pickup_location')} ➔ {b.get('dropoff_location')}
                - **Scheduled:** {b.get('start_datetime', '')[:16]}
                - **Notes:** {b.get('special_notes') or 'None'}
                """)
            with col2:
                st.markdown(f"""
                - **Trip Fare:** {format_inr(b.get('base_trip_fare', 0))} (Direct to driver)
                - **Platform Fee:** ₹20.00 ({b.get('fee_payment_status', 'paid').upper()})
                - **Status:** **{cur_status.upper()}**
                """)

                # Admin override status
                new_status = st.selectbox("Admin Status Override", [s.value for s in BookingStatus], index=[s.value for s in BookingStatus].index(cur_status), key=f"adm_status_sel_{b_id}")
                if st.button("Apply Status Override", key=f"adm_save_{b_id}"):
                    BookingService.update_booking_status(b_id, new_status, admin_override=True)
                    st.success(f"Status overridden to {new_status}")
                    st.rerun()


# ============================================================================
# TAB 4: MANAGE COMPLAINTS & GRIEVANCES
# ============================================================================
def render_manage_complaints():
    st.markdown("### ⚖️ Campus Grievance & Dispute Resolution Desk")
    st.caption("Review, investigate, and resolve student complaints with official admin notes.")
    complaints = ComplaintService.get_all_complaints()

    # Severity distribution
    c_open = len([c for c in complaints if c.get("status") in ("open", "under_investigation")])
    c_resolved = len([c for c in complaints if c.get("status") == "resolved"])

    c1, c2 = st.columns(2)
    c1.metric("Open / In-Review Tickets", c_open)
    c2.metric("Resolved Disputes", c_resolved)

    if not complaints:
        st.info("No complaints reported.")
        return

    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

    for c in complaints:
        c_id = c.get("id")
        cur_status = c.get("status", "open")
        
        status_tag = {
            "open": ("🟡 Open", "#FEF3C7", "#92400E"),
            "under_investigation": ("🔵 In Review", "#DBEAFE", "#1E40AF"),
            "resolved": ("🟢 Resolved", "#D1FAE5", "#065F46"),
            "dismissed": ("⚪ Dismissed", "#F1F5F9", "#475569")
        }.get(cur_status, ("🟡 Open", "#FEF3C7", "#92400E"))

        with st.container(border=True):
            # Header Row
            col_h1, col_h2 = st.columns([3, 1])
            with col_h1:
                st.markdown(
                    f"<span style='background:{status_tag[1]}; color:{status_tag[2]}; padding:3px 10px; border-radius:9999px; font-weight:700; font-size:0.8rem;'>"
                    f"{status_tag[0]}</span> "
                    f"<strong style='font-size:1.1rem; color:#0F172A; margin-left:8px;'>"
                    f"Ticket #{c_id[:8]} — {c.get('complaint_type', '').replace('_', ' ').title()}</strong>",
                    unsafe_allow_html=True
                )
            with col_h2:
                created = c.get("created_at", "")[:10]
                st.markdown(f"<div style='text-align:right; font-size:0.8rem; color:#64748B;'>Filed: {created}</div>", unsafe_allow_html=True)

            # Details
            st.markdown(f"""
            <div style="background:#F8FAFC; border:1px solid #E2E8F0; border-radius:8px; padding:12px; margin:10px 0;">
                <div style="color:#0F172A; font-size:0.95rem; font-weight:600; margin-bottom:4px;">
                    Student: <strong>{c.get('raised_by_name')}</strong> ({c.get('raised_by_email', '')})
                </div>
                <div style="color:#475569; font-size:0.88rem;">
                    Driver / Partner: <strong>{c.get('target_name', 'N/A')}</strong> • Route: <strong>{c.get('pickup_location', 'Gate 2')} ➔ {c.get('dropoff_location', 'Transit')}</strong>
                </div>
                <div style="color:#1E293B; font-size:0.95rem; margin-top:8px; background:#FFFFFF; border:1px solid #E2E8F0; padding:10px; border-radius:6px;">
                    <strong>Issue Description:</strong> {c.get('description')}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Admin Resolution Form
            col1, col2, col3 = st.columns([1.5, 3, 1.2])
            with col1:
                status_index = [s.value for s in ComplaintStatus].index(cur_status) if cur_status in [s.value for s in ComplaintStatus] else 0
                status_sel = st.selectbox("Resolution State", [s.value for s in ComplaintStatus], index=status_index, format_func=lambda x: x.replace("_", " ").title(), key=f"comp_st_{c_id}")
            with col2:
                notes_txt = st.text_input("Admin Resolution Notes", value=c.get("admin_notes", ""), placeholder="e.g. Warning issued to driver, full refund processed", key=f"comp_notes_{c_id}")
            with col3:
                st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
                if st.button("Update Ticket", key=f"btn_comp_up_{c_id}", type="primary", use_container_width=True):
                    ComplaintService.update_complaint_status(c_id, status_sel, notes_txt)
                    st.toast("Dispute resolution updated successfully!", icon="✅")
                    st.rerun()


# ============================================================================
# TAB 5: MANAGE RATINGS & REVIEWS
# ============================================================================
def render_manage_ratings():
    st.markdown("### ⭐ Partner Ratings, Leaderboards & Moderation")
    st.caption("Live rankings based on verified student trip feedback and completed rides.")
    reviews = BookingService.get_all_reviews()
    drivers = VehicleService.get_all_drivers_kyc()

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("#### 🏆 Driver Performance Leaderboard")
        sorted_drivers = sorted(drivers, key=lambda x: float(x.get("rating", 0)), reverse=True)
        for i, d in enumerate(sorted_drivers, 1):
            r = float(d.get("rating", 5.0))
            badge_icon = "🥇" if i == 1 else ("🥈" if i == 2 else ("🥉" if i == 3 else f"#{i}"))
            warning_tag = '<span style="color:#DC2626; font-size:0.75rem; font-weight:700; background:#FEE2E2; padding:2px 6px; border-radius:4px; margin-left:6px;">⚠️ UNDERPERFORMING</span>' if r < 3.5 else ''
            
            with st.container(border=True):
                col_lb1, col_lb2 = st.columns([3.5, 1.5])
                with col_lb1:
                    st.markdown(f"""
                    <div style="display:flex; align-items:center;">
                        <span style="font-size:1.2rem; margin-right:8px;">{badge_icon}</span>
                        <div>
                            <strong style="color:#0F172A; font-size:1rem;">{d.get('business_name') or d.get('full_name')}</strong> {warning_tag}<br/>
                            <span style="font-size:0.8rem; color:#64748B;">{d.get('total_completed_trips', 0)} completed trips • {d.get('provider_type', 'Taxi Union').replace('_', ' ').title()}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                with col_lb2:
                    st.markdown(f"""
                    <div style="text-align:right; font-size:1.2rem; font-weight:800; color:#D97706;">
                        ⭐ {r:.1f}
                    </div>
                    """, unsafe_allow_html=True)

    with col2:
        st.markdown("#### 💬 Student Reviews Stream")
        if not reviews:
            st.info("No student reviews recorded yet.")
        else:
            for r in reviews:
                rating_num = int(r.get('rating', 5))
                with st.container(border=True):
                    col_r1, col_r2 = st.columns([3, 2])
                    with col_r1:
                        st.markdown(f"<strong style='color:#0F172A; font-size:0.95rem;'>{r.get('student_name', 'Student')}</strong>", unsafe_allow_html=True)
                    with col_r2:
                        st.markdown(f"<div style='text-align:right; color:#D97706; font-weight:700;'>{'⭐' * rating_num}</div>", unsafe_allow_html=True)

                    st.markdown(f"""
                    <div style="color:#334155; font-size:0.9rem; font-style:italic; margin:6px 0;">"{r.get('comment', 'Great service!')}"</div>
                    <div style="font-size:0.75rem; color:#64748B;">For <strong>{r.get('provider_name', 'Verified Partner')}</strong> • {r.get('created_at', '')[:10]}</div>
                    """, unsafe_allow_html=True)


# ============================================================================
# TAB 6: INTERACTIVE ANALYTICS & VISUALIZATIONS
# ============================================================================
def render_analytics_dashboard():
    st.markdown("### 📊 Live Telemetry & Campus Mobility Analytics")
    st.caption("Real-time data aggregated directly from user interactions, active bookings, and fleet telemetry.")

    # Financial & Volume KPIs
    fin = AnalyticsService.get_financial_summary()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="stCard" style="padding:16px;">
            <span style="font-size:0.75rem; color:#64748B; font-weight:700; text-transform:uppercase;">Platform Revenue</span>
            <div style="font-size:1.6rem; font-weight:800; color:#2563EB; margin:4px 0;">{format_inr(fin['platform_convenience_fees'])}</div>
            <span style="font-size:0.75rem; color:#059669; font-weight:600;">₹20 / Booking Fee</span>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="stCard" style="padding:16px;">
            <span style="font-size:0.75rem; color:#64748B; font-weight:700; text-transform:uppercase;">Driver Gross Payout</span>
            <div style="font-size:1.6rem; font-weight:800; color:#059669; margin:4px 0;">{format_inr(fin['total_driver_earnings_retained'])}</div>
            <span style="font-size:0.75rem; color:#059669; font-weight:600;">100% Retained (0% Commission)</span>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="stCard" style="padding:16px;">
            <span style="font-size:0.75rem; color:#64748B; font-weight:700; text-transform:uppercase;">Total Bookings</span>
            <div style="font-size:1.6rem; font-weight:800; color:#0F172A; margin:4px 0;">{fin['total_bookings_count']}</div>
            <span style="font-size:0.75rem; color:#64748B;">{fin['paid_bookings_count']} Confirmed Rides</span>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="stCard" style="padding:16px;">
            <span style="font-size:0.75rem; color:#64748B; font-weight:700; text-transform:uppercase;">Student Retention</span>
            <div style="font-size:1.6rem; font-weight:800; color:#7C3AED; margin:4px 0;">{fin['repeat_student_booking_rate']}%</div>
            <span style="font-size:0.75rem; color:#64748B;">Repeat student bookings</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

    # Chart Row 1: Funnel Drop-off Flow & Vehicle Category Distribution
    col_ch1, col_ch2 = st.columns([1, 1])

    with col_ch1:
        st.markdown("#### 🔻 Live Conversion Funnel (Drop-Off Flow)")
        funnel_df = AnalyticsService.get_funnel_metrics()
        
        fig_funnel = go.Figure(go.Funnel(
            y=funnel_df["Stage"],
            x=funnel_df["Users"],
            textinfo="value+percent initial",
            marker=dict(color=["#1E40AF", "#2563EB", "#60A5FA", "#F59E0B", "#10B981"]),
            connector=dict(line=dict(color="#CBD5E1", width=1))
        ))
        fig_funnel.update_layout(
            template="plotly_white",
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#FFFFFF",
            margin=dict(l=10, r=10, t=10, b=10),
            height=320
        )
        st.plotly_chart(fig_funnel, use_container_width=True)

    with col_ch2:
        st.markdown("#### 🚗 Fleet Demand Split (Cabs vs Self-Drive)")
        dist_df = AnalyticsService.get_vehicle_segment_distribution()
        
        fig_donut = px.pie(
            dist_df,
            names="Segment Category",
            values="Bookings",
            hole=0.5,
            color_discrete_sequence=["#2563EB", "#10B981", "#F59E0B"]
        )
        fig_donut.update_layout(
            template="plotly_white",
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#FFFFFF",
            margin=dict(l=10, r=10, t=10, b=10),
            height=320
        )
        st.plotly_chart(fig_donut, use_container_width=True)

    # Chart Row 2: Popular Destination Bar Chart & Live Event Feed
    col_ch3, col_ch4 = st.columns([1, 1])

    with col_ch3:
        st.markdown("#### 📍 Top Campus Transit Destinations")
        routes_df = AnalyticsService.get_route_popularity()
        
        fig_routes = px.bar(
            routes_df,
            x="Trip Volume",
            y="Destination",
            orientation="h",
            color="Trip Volume",
            color_continuous_scale="Blues"
        )
        fig_routes.update_layout(
            template="plotly_white",
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#FFFFFF",
            yaxis=dict(autorange="reversed"),
            margin=dict(l=10, r=10, t=10, b=10),
            height=340
        )
        st.plotly_chart(fig_routes, use_container_width=True)

    with col_ch4:
        st.markdown("#### ⚡ Real-Time User Clickstream & Telemetry Feed")
        event_df = AnalyticsService.get_live_event_stream(limit=10)
        st.dataframe(event_df, use_container_width=True, height=300, hide_index=True)


def render_manage_pricing():
    st.markdown("### 💰 Campus Pricing & Base Fares Administrator")
    st.caption("Configure the flat/tiered fare structures for campus cabs and self-drive rentals.")

    # Load current pricing config
    cab_rules = PricingService.get_cab_fare_rules()
    self_drive_rates = PricingService.get_self_drive_hourly_rates()

    st.markdown("---")
    
    col_p1, col_p2 = st.columns(2)
    
    # 🚖 CAB PRICING RULES FORM
    with col_p1:
        st.markdown("#### 🚖 Campus Cab Fare Rules")
        st.caption("Used dynamically based on distance calculations originating/terminating at GIM Gate 2.")
        
        updated_cab_rules = {}
        for tier, rule in cab_rules.items():
            st.markdown(f"**{tier} Class**")
            col_t1, col_t2 = st.columns(2)
            with col_t1:
                base = st.number_input(
                    f"Base Fare (₹) - {tier}",
                    min_value=0.0,
                    max_value=1000.0,
                    value=float(rule.get("base_fare", 80.0)),
                    key=f"cab_base_{tier}"
                )
            with col_t2:
                rate = st.number_input(
                    f"Rate per Km (₹) - {tier}",
                    min_value=0.0,
                    max_value=200.0,
                    value=float(rule.get("rate_per_km", 22.0)),
                    key=f"cab_rate_{tier}"
                )
            updated_cab_rules[tier] = {"base_fare": base, "rate_per_km": rate}
            
    # 🛵 SELF-DRIVE RENTAL RATES FORM
    with col_p2:
        st.markdown("#### 🛵 Self-Drive Rental Hourly Rates")
        st.caption("Flat rate charged per hour of rental duration for cars, bikes, and scooties.")
        
        updated_self_drive_rates = {}
        for vehicle_type, current_rate in self_drive_rates.items():
            icon = {
                "SUV": "🚗",
                "Sedan": "🚗",
                "Hatchback": "🚗",
                "Bike": "🛵",
                "Scooty": "🛵"
            }.get(vehicle_type, "🚙")
            
            rate = st.number_input(
                f"{icon} {vehicle_type} Rate (₹/hour)",
                min_value=0.0,
                max_value=1000.0,
                value=float(current_rate),
                key=f"sd_rate_{vehicle_type}"
            )
            updated_self_drive_rates[vehicle_type] = rate

    st.markdown("<div style='height:15px;'></div>", unsafe_allow_html=True)
    
    save_pricing = st.button("💾 Save Global Pricing Settings", type="primary", use_container_width=True)
    
    if save_pricing:
        ok = PricingService.update_pricing(updated_cab_rules, updated_self_drive_rates)
        if ok:
            st.toast("Pricing updated successfully across GIM!", icon="🎉")
            st.rerun()
        else:
            st.error("Failed to save pricing configuration changes.")
