"""
Secure Multi-Role Authentication & Registration View for GIM Mobility Aggregator.
100% Mobile-First / Mobile-Only optimized layout.
"""
import streamlit as st
from src.config import Role, GIM_PROGRAMS, STUDENT_EMAIL_DOMAIN
from src.services.auth_service import AuthService


def render_login_page():
    """Render 100% mobile-first secure authentication and profile creation gateway."""
    
    # Compact Mobile Header
    st.markdown("""
    <div style="text-align: center; padding: 14px 12px 10px 12px; margin-bottom: 8px;">
        <div style="display: inline-flex; align-items: center; justify-content: center; width: 48px; height: 48px; background: #EFF6FF; border-radius: 14px; margin-bottom: 8px; border: 1px solid #BFDBFE;">
            <span style="font-size: 1.5rem;">🚗</span>
        </div>
        <h1 style="margin: 0; color: #0F172A; font-family: 'Outfit', sans-serif; font-size: 1.8rem; font-weight: 800; letter-spacing: -0.03em;">
            GIM <span style="color: #2563EB;">Mobility</span>
        </h1>
        <p style="color: #64748B; font-size: 0.85rem; margin: 4px auto 0 auto; font-weight: 500;">
            Goa Institute of Management • Campus Rides & Rentals
        </p>
    </div>
    """, unsafe_allow_html=True)

    auth_tabs = st.tabs(["🔑 Sign In", "✨ Create Account"])

    # ====================================================================
    # TAB 1: SIGN IN
    # ====================================================================
    with auth_tabs[0]:
        st.markdown("""
        <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 14px 16px; margin-top: 6px; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.03);">
            <div style="color: #0F172A; font-size: 1.05rem; font-weight: 700;">Welcome back</div>
            <div style="color: #64748B; font-size: 0.8rem;">Select your profile type to sign in.</div>
        </div>
        """, unsafe_allow_html=True)

        role_tabs = st.tabs(["Student", "Partner", "Admin"])

        # ---------------- STUDENT SIGN IN ----------------
        with role_tabs[0]:
            with st.form("login_form_student"):
                user_email = st.text_input(
                    "Student Email",
                    placeholder="name.roll@gim.ac.in",
                    help="Official @gim.ac.in student email"
                )
                user_password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Enter your password"
                )
                st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
                submit_student = st.form_submit_button("Sign In as Student", use_container_width=True, type="primary")

                if submit_student:
                    _handle_login("student", user_email, user_password)

        # ---------------- SERVICE PROVIDER SIGN IN ----------------
        with role_tabs[1]:
            with st.form("login_form_provider"):
                user_email = st.text_input(
                    "Partner Email",
                    placeholder="driver@cabservice.com",
                    help="Registered email for transport partner account"
                )
                user_password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Enter your password"
                )
                st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
                submit_provider = st.form_submit_button("Sign In as Partner", use_container_width=True, type="primary")

                if submit_provider:
                    _handle_login("provider", user_email, user_password)

        # ---------------- ADMIN SIGN IN ----------------
        with role_tabs[2]:
            with st.form("login_form_admin"):
                user_email = st.text_input(
                    "Admin Email",
                    placeholder="transport.admin@gim.ac.in",
                    help="Campus Transport Committee administrative login"
                )
                user_password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Enter your password"
                )
                st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
                submit_admin = st.form_submit_button("Sign In as Admin", use_container_width=True, type="primary")

                if submit_admin:
                    _handle_login("admin", user_email, user_password)

    # ====================================================================
    # TAB 2: CREATE ACCOUNT / REGISTER
    # ====================================================================
    with auth_tabs[1]:
        st.markdown("""
        <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 14px 16px; margin-top: 6px; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.03);">
            <div style="color: #0F172A; font-size: 1.05rem; font-weight: 700;">Create a profile</div>
            <div style="color: #64748B; font-size: 0.8rem;">Choose your account type below.</div>
        </div>
        """, unsafe_allow_html=True)

        reg_tabs = st.tabs(["Student", "Partner"])

        # ---------------- STUDENT REGISTRATION ----------------
        with reg_tabs[0]:
            st.caption(f"Requires official `{STUDENT_EMAIL_DOMAIN}` address.")

            with st.form("student_registration_form"):
                reg_full_name = st.text_input("Full Name", placeholder="e.g. Sameer Verma")
                reg_email = st.text_input(
                    "GIM Student Email",
                    placeholder=f"e.g. yourname.k25{STUDENT_EMAIL_DOMAIN}"
                )
                reg_phone = st.text_input("Mobile Phone", placeholder="e.g. +91 98221 00000")
                reg_program = st.selectbox("Academic Program", GIM_PROGRAMS)

                reg_pw1 = st.text_input("Create Password", type="password", placeholder="Min 6 characters")
                reg_pw2 = st.text_input("Confirm Password", type="password", placeholder="Re-enter password")

                submit_reg_student = st.form_submit_button(
                    "Create Student Profile",
                    use_container_width=True,
                    type="primary"
                )

                if submit_reg_student:
                    if not reg_full_name.strip():
                        st.toast("Please enter your full name.", icon="⚠️")
                    elif not reg_email.strip():
                        st.toast("Please enter your GIM student email.", icon="⚠️")
                    elif not reg_email.strip().lower().endswith(STUDENT_EMAIL_DOMAIN):
                        st.toast(f"Email must end with {STUDENT_EMAIL_DOMAIN}.", icon="⚠️")
                    elif not reg_phone.strip() or len(reg_phone.strip()) < 10:
                        st.toast("Please enter a valid 10-digit phone number.", icon="⚠️")
                    elif len(reg_pw1) < 6:
                        st.toast("Password must be at least 6 characters.", icon="⚠️")
                    elif reg_pw1 != reg_pw2:
                        st.toast("Passwords do not match.", icon="⚠️")
                    else:
                        try:
                            success, msg, new_profile = AuthService.register_student(
                                full_name=reg_full_name,
                                email=reg_email,
                                phone=reg_phone,
                                program=reg_program,
                                password=reg_pw1
                            )
                            if success and new_profile:
                                AuthService.set_current_user(new_profile)
                                st.toast("Profile created successfully!", icon="🎉")
                                st.rerun()
                            else:
                                st.error(msg)
                        except Exception as e:
                            st.toast("Unable to complete registration. Please try again.", icon="⚠️")

        # ---------------- SERVICE PROVIDER REGISTRATION ----------------
        with reg_tabs[1]:
            st.caption("Verified local drivers and rental agencies. 0% Commission.")

            with st.form("provider_registration_form"):
                pv_full_name = st.text_input("Contact Name", placeholder="e.g. Ramesh Naik")
                pv_business = st.text_input("Business / Taxi Union Name", placeholder="e.g. Sanquelim Cabs")
                pv_email = st.text_input("Email Address", placeholder="e.g. ramesh.cabs@gmail.com")
                pv_phone = st.text_input("Mobile Phone", placeholder="e.g. +91 98220 11223")

                pv_type = st.selectbox(
                    "Service Type",
                    options=["individual_driver", "rental_agency"],
                    format_func=lambda x: {
                        "individual_driver": "🚖 Cab Service (Chauffeur)",
                        "rental_agency": "🚗 Self-Drive Rentals (Cars / Bikes)"
                    }.get(x, x)
                )
                pv_license = st.text_input("Driving License / GST Reg No.", placeholder="e.g. GA-04-20210008899")

                pv_pw1 = st.text_input("Create Password", type="password", placeholder="Min 6 characters")
                pv_pw2 = st.text_input("Confirm Password", type="password", placeholder="Re-enter password")

                submit_reg_pv = st.form_submit_button(
                    "Create Partner Profile",
                    use_container_width=True,
                    type="primary"
                )

                if submit_reg_pv:
                    if not pv_full_name.strip():
                        st.toast("Please provide contact person's name.", icon="⚠️")
                    elif not pv_business.strip():
                        st.toast("Please provide your business name.", icon="⚠️")
                    elif not pv_email.strip() or "@" not in pv_email:
                        st.toast("Please enter a valid email address.", icon="⚠️")
                    elif not pv_phone.strip() or len(pv_phone.strip()) < 10:
                        st.toast("Please enter a valid phone number.", icon="⚠️")
                    elif not pv_license.strip():
                        st.toast("Please enter your commercial license or registration number.", icon="⚠️")
                    elif len(pv_pw1) < 6:
                        st.toast("Password must be at least 6 characters.", icon="⚠️")
                    elif pv_pw1 != pv_pw2:
                        st.toast("Passwords do not match.", icon="⚠️")
                    else:
                        try:
                            success, msg, new_provider = AuthService.register_service_provider(
                                full_name=pv_full_name,
                                email=pv_email,
                                phone=pv_phone,
                                business_name=pv_business,
                                provider_type=pv_type,
                                license_number=pv_license,
                                password=pv_pw1
                            )
                            if success and new_provider:
                                AuthService.set_current_user(new_provider)
                                st.toast("Partner profile registered successfully!", icon="🎉")
                                st.rerun()
                            else:
                                st.error(msg)
                        except Exception as e:
                            st.toast("Unable to submit registration. Please try again.", icon="⚠️")


def _handle_login(role_choice: str, email: str, password: str):
    """Process login verification and set user session."""
    if not email or not email.strip():
        st.toast("Please enter your email address.", icon="⚠️")
    elif not password or not password.strip():
        st.toast("Please enter your password.", icon="⚠️")
    else:
        try:
            success, message, auth_user = AuthService.authenticate_user(
                role_type=role_choice,
                email=email,
                password=password
            )
            if success and auth_user:
                AuthService.set_current_user(auth_user)
                st.toast(f"Welcome back, {auth_user.get('full_name')}!", icon="✅")
                st.rerun()
            else:
                st.toast(message, icon="❌")
                st.error(message)
        except Exception as e:
            st.toast("Authentication service unavailable. Please try again.", icon="⚠️")
