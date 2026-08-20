"""
Secure Multi-Role Authentication & Registration View for GIM Mobility Aggregator.
Clean, modern consumer light theme with horizontal tabs for role selection (Student, Service Provider, Admin).
"""
import streamlit as st
from src.config import Role, GIM_PROGRAMS, STUDENT_EMAIL_DOMAIN
from src.services.auth_service import AuthService


def render_login_page():
    """Render the consumer-grade secure authentication and profile creation gateway."""
    
    # Modern Hero Header
    st.markdown("""
    <div style="text-align: center; padding: 24px 12px 16px 12px; margin-bottom: 12px;">
        <div style="display: inline-flex; align-items: center; justify-content: center; width: 56px; height: 56px; background: #EFF6FF; border-radius: 16px; margin-bottom: 12px; border: 1px solid #BFDBFE;">
            <span style="font-size: 1.8rem;">🚗</span>
        </div>
        <h1 style="margin: 0; color: #0F172A; font-family: 'Outfit', sans-serif; font-size: 2.2rem; font-weight: 800; letter-spacing: -0.03em;">
            GIM <span style="color: #2563EB;">Mobility</span>
        </h1>
        <p style="color: #475569; font-size: 0.95rem; margin: 6px auto 0 auto; max-width: 480px; font-weight: 500;">
            Goa Institute of Management • Verified Campus Rides & Rentals
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Responsive Centered Form Container
    col_left, col_center, col_right = st.columns([1, 2.2, 1])

    with col_center:
        auth_tabs = st.tabs(["🔑 Sign In", "✨ Create Account"])

        # ====================================================================
        # TAB 1: SIGN IN
        # ====================================================================
        with auth_tabs[0]:
            st.markdown("""
            <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 14px; padding: 18px 20px; margin-top: 10px; margin-bottom: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.04);">
                <h3 style="margin: 0 0 4px 0; color: #0F172A; font-size: 1.2rem; font-weight: 700;">Sign in to your account</h3>
                <p style="color: #64748B; font-size: 0.85rem; margin: 0;">
                    Select your profile tab below to continue.
                </p>
            </div>
            """, unsafe_allow_html=True)

            role_tabs = st.tabs(["Student", "Service Provider", "Admin"])

            # ---------------- STUDENT SIGN IN ----------------
            with role_tabs[0]:
                with st.form("login_form_student"):
                    user_email = st.text_input(
                        "Student Email",
                        placeholder="e.g. name.roll@gim.ac.in",
                        help="Must be your official @gim.ac.in student email"
                    )
                    user_password = st.text_input(
                        "Password",
                        type="password",
                        placeholder="Enter your account password"
                    )
                    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
                    submit_student = st.form_submit_button("Sign In as Student", use_container_width=True, type="primary")

                    if submit_student:
                        _handle_login("student", user_email, user_password)

            # ---------------- SERVICE PROVIDER SIGN IN ----------------
            with role_tabs[1]:
                with st.form("login_form_provider"):
                    user_email = st.text_input(
                        "Service Provider Email",
                        placeholder="e.g. driver@cabservice.com",
                        help="Registered email for transport provider account"
                    )
                    user_password = st.text_input(
                        "Password",
                        type="password",
                        placeholder="Enter your account password"
                    )
                    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
                    submit_provider = st.form_submit_button("Sign In as Service Provider", use_container_width=True, type="primary")

                    if submit_provider:
                        _handle_login("provider", user_email, user_password)

            # ---------------- ADMIN SIGN IN ----------------
            with role_tabs[2]:
                with st.form("login_form_admin"):
                    user_email = st.text_input(
                        "Admin Email",
                        placeholder="e.g. transport.admin@gim.ac.in",
                        help="Campus Transport Committee administrative login"
                    )
                    user_password = st.text_input(
                        "Password",
                        type="password",
                        placeholder="Enter your account password"
                    )
                    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
                    submit_admin = st.form_submit_button("Sign In as Admin", use_container_width=True, type="primary")

                    if submit_admin:
                        _handle_login("admin", user_email, user_password)

        # ====================================================================
        # TAB 2: CREATE ACCOUNT / REGISTER
        # ====================================================================
        with auth_tabs[1]:
            st.markdown("""
            <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 14px; padding: 18px 20px; margin-top: 10px; margin-bottom: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.04);">
                <h3 style="margin: 0 0 4px 0; color: #0F172A; font-size: 1.2rem; font-weight: 700;">Create a new profile</h3>
                <p style="color: #64748B; font-size: 0.85rem; margin: 0;">
                    Select your profile type tab below to register.
                </p>
            </div>
            """, unsafe_allow_html=True)

            reg_tabs = st.tabs(["Student", "Service Provider"])

            # ---------------- STUDENT REGISTRATION ----------------
            with reg_tabs[0]:
                st.caption(f"Domain restricted: Requires an official `{STUDENT_EMAIL_DOMAIN}` address.")

                with st.form("student_registration_form"):
                    reg_full_name = st.text_input("Full Name", placeholder="e.g. Sameer Verma")
                    reg_email = st.text_input(
                        "GIM Student Email",
                        placeholder=f"e.g. yourname.k25{STUDENT_EMAIL_DOMAIN}"
                    )
                    
                    col_p1, col_p2 = st.columns(2)
                    with col_p1:
                        reg_phone = st.text_input("Mobile Phone", placeholder="e.g. +91 98221 00000")
                    with col_p2:
                        reg_program = st.selectbox("Academic Program", GIM_PROGRAMS)

                    col_pw1, col_pw2 = st.columns(2)
                    with col_pw1:
                        reg_pw1 = st.text_input("Create Password", type="password", placeholder="Min 6 characters")
                    with col_pw2:
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
                                    st.toast("Profile created successfully! Welcome to GIM Mobility.", icon="🎉")
                                    st.rerun()
                                else:
                                    st.error(msg)
                            except Exception as e:
                                st.toast("Unable to complete registration. Please try again.", icon="⚠️")

            # ---------------- SERVICE PROVIDER REGISTRATION ----------------
            with reg_tabs[1]:
                st.caption("Verified local drivers and rental agencies. 0% Commission.")

                with st.form("provider_registration_form"):
                    col_pv1, col_pv2 = st.columns(2)
                    with col_pv1:
                        pv_full_name = st.text_input("Contact Name", placeholder="e.g. Ramesh Naik")
                    with col_pv2:
                        pv_business = st.text_input("Business / Taxi Union Name", placeholder="e.g. Sanquelim Cabs")

                    col_pv3, col_pv4 = st.columns(2)
                    with col_pv3:
                        pv_email = st.text_input("Email Address", placeholder="e.g. ramesh.cabs@gmail.com")
                    with col_pv4:
                        pv_phone = st.text_input("Mobile Phone", placeholder="e.g. +91 98220 11223")

                    col_pv5, col_pv6 = st.columns(2)
                    with col_pv5:
                        pv_type = st.selectbox(
                            "Service Type",
                            options=["individual_driver", "rental_agency"],
                            format_func=lambda x: {
                                "individual_driver": "🚖 Cab Service (Chauffeur)",
                                "rental_agency": "🚗 Self-Drive Rentals (Cars / Bikes)"
                            }.get(x, x)
                        )
                    with col_pv6:
                        pv_license = st.text_input("Driving License / GST Reg No.", placeholder="e.g. GA-04-20210008899")

                    col_pvw1, col_pvw2 = st.columns(2)
                    with col_pvw1:
                        pv_pw1 = st.text_input("Create Password", type="password", placeholder="Min 6 characters")
                    with col_pvw2:
                        pv_pw2 = st.text_input("Confirm Password", type="password", placeholder="Re-enter password")

                    submit_reg_pv = st.form_submit_button(
                        "Create Service Provider Profile",
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
                                    st.toast("Service provider profile registered successfully!", icon="🎉")
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
