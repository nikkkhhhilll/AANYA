"""
GIM Campus Mobility Aggregator (AANYA Mobility Engine)
Production-grade Streamlit Application Entrypoint & Session Router.
Clean, modern, vibrant light theme (Uber/Airbnb style).
"""
import streamlit as st
from src.config import Role, CUSTOM_CSS
from src.services.auth_service import AuthService
from src.views.login_view import render_login_page
from src.views.student_view import render_student_portal
from src.views.provider_view import render_provider_portal
from src.views.admin_view import render_admin_portal


def main():
    st.set_page_config(
        page_title="Ride Smart • Campus Rides & Rentals",
        page_icon="🚗",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    # Inject global CSS styling
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    # Initialize session state
    AuthService.init_session_state()

    # If user is not authenticated, show the Secure Login / Register Gateway
    if not st.session_state.get("is_authenticated", False):
        render_sidebar(authenticated=False)
        render_login_page()
        return

    # Authenticated user workflow
    current_user = st.session_state.get("current_user") or {}
    current_role = current_user.get("role", Role.STUDENT.value)

    # Render Sidebar with User Profile Info & Logout Action
    render_sidebar(authenticated=True)

    # Main Router based on authenticated role
    if current_role == Role.STUDENT.value:
        render_student_portal(current_user)
    elif current_role in (Role.DRIVER.value, Role.PROVIDER.value):
        render_provider_portal(current_user)
    elif current_role == Role.ADMIN.value:
        render_admin_portal(current_user)
    else:
        st.error(f"Unrecognized profile role '{current_role}'. Please sign in again.")
        if st.button("Return to Sign In", type="primary"):
            AuthService.logout()


def render_sidebar(authenticated: bool = True):
    """Render clean production sidebar with user profile badge and quick actions."""
    with st.sidebar:
        st.markdown("""
        <div style="display:flex; align-items:center; gap:10px; padding:12px 0 16px 0;">
            <div style="display:flex; align-items:center; justify-content:center; width:40px; height:40px; background:var(--bg-surface); border-radius:10px; border:1px solid var(--border-subtle);">
                <span style="font-size:1.3rem;">🚗</span>
            </div>
            <div>
                <h3 style="margin:0; font-size:1.2rem; font-weight:800; color:var(--text-primary); line-height:1.1;">
                    Ride <span style="color:#2563EB;">Smart</span>
                </h3>
                <span style="font-size:0.75rem; color:var(--text-secondary); font-weight:500;">
                    Sanquelim Campus
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        if authenticated:
            current_user = st.session_state.get("current_user", {})
            user_name = current_user.get("full_name", "Campus User")
            user_email = current_user.get("email", "")
            user_role = current_user.get("role", "student")
            user_prog = current_user.get("program") or current_user.get("business_name") or "GIM Community"

            role_tag = {
                Role.STUDENT.value: ("🎓 Verified Student", "#D1FAE5", "#065F46"),
                Role.DRIVER.value: ("🚕 Verified Driver", "#EFF6FF", "#1D4ED8"),
                Role.PROVIDER.value: ("🚗 Rental Partner", "#FEF3C7", "#92400E"),
                Role.ADMIN.value: ("🛡️ Transport Admin", "#FEE2E2", "#991B1B")
            }.get(user_role, ("👤 User", "#F1F5F9", "#475569"))

            st.markdown(f"""
            <div style="background:var(--bg-surface); border:1px solid var(--border-subtle); border-radius:12px; padding:14px; margin-bottom:16px; box-shadow:0 2px 4px rgba(0,0,0,0.03);">
                <span style="background:{role_tag[1]}; color:{role_tag[2]}; padding:2px 8px; border-radius:9999px; font-weight:700; font-size:0.72rem; display:inline-block; margin-bottom:6px;">
                    {role_tag[0]}
                </span>
                <div style="font-weight:700; font-size:1.05rem; color:var(--text-primary); line-height:1.2;">
                    {user_name}
                </div>
                <div style="font-size:0.8rem; color:var(--text-secondary); margin-top:2px;">
                    {user_email}
                </div>
                <div style="font-size:0.75rem; color:var(--text-muted); margin-top:4px;">
                    📍 {user_prog}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Log Out Button
            if st.button("🚪 Sign Out", use_container_width=True, type="secondary"):
                AuthService.logout()

            st.divider()

            # Campus Hotline Card
            st.markdown("""
            <div style="background:#F8FAFC; border:1px solid #E2E8F0; border-radius:10px; padding:12px;">
                <span style="font-size:0.75rem; font-weight:700; color:#475569; text-transform:uppercase;">Campus Transport Desk</span>
                <div style="font-size:0.85rem; color:#0F172A; font-weight:600; margin-top:4px;">📞 +91 832 2366700</div>
                <div style="font-size:0.75rem; color:#64748B;">GIM Gate No. 2 Help Desk</div>
            </div>
            """, unsafe_allow_html=True)

        else:
            st.markdown("""
            <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:12px; padding:14px; text-align:center; box-shadow:0 2px 4px rgba(0,0,0,0.03);">
                <span style="font-size:0.85rem; color:#2563EB; font-weight:700;">🔒 Secure Access</span><br/>
                <span style="font-size:0.75rem; color:#64748B; display:block; margin-top:4px;">Please sign in with your @gim.ac.in account or partner credentials to book rides.</span>
            </div>
            """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
