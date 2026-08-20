"""
Authentication, Authorization, and Session Management Service for GIM Mobility.
Enforces @gim.ac.in domain validation for students and provides multi-role sessions.
"""
import uuid
import datetime
import streamlit as st
from typing import Optional, Dict, Any, List, Tuple
from src.config import Role, STUDENT_EMAIL_DOMAIN, hash_password, verify_password, DEFAULT_DEMO_PASSWORD
from src.db import DBService


class AuthService:
    """Authentication and session state manager."""
    _DYNAMIC_HASH_CACHE: Dict[str, str] = {}

    @staticmethod
    def validate_student_email(email: str) -> Tuple[bool, str]:
        """
        Enforce strict @gim.ac.in domain for student accounts (Security NFR).
        """
        if not email or not isinstance(email, str):
            return False, "Email address is required."
        
        email = email.strip().lower()
        if not email.endswith(STUDENT_EMAIL_DOMAIN):
            return False, f"Access restricted: Student email must belong to the '{STUDENT_EMAIL_DOMAIN}' domain."
        
        return True, "Email validated successfully."

    @staticmethod
    def get_all_users() -> List[Dict[str, Any]]:
        """Fetch all profiles in the system."""
        return DBService.query("profiles", order_by="created_at")

    @staticmethod
    def get_students() -> List[Dict[str, Any]]:
        """Fetch all registered student profiles."""
        return DBService.query("profiles", filters={"role": Role.STUDENT.value}, order_by="full_name")

    @staticmethod
    def get_providers_and_drivers() -> List[Dict[str, Any]]:
        """Fetch all drivers and providers enriched with business metadata."""
        profiles = DBService.query("profiles", order_by="full_name")
        drivers = {d["id"]: d for d in DBService.query("drivers")}
        results = []
        for p in profiles:
            if p.get("role") in (Role.DRIVER.value, Role.PROVIDER.value):
                p_copy = dict(p)
                d_info = drivers.get(p["id"], {})
                p_copy.update({
                    "business_name": d_info.get("business_name") or p.get("full_name"),
                    "provider_type": d_info.get("provider_type", "individual_driver"),
                    "license_number": d_info.get("license_number", ""),
                    "is_verified": bool(d_info.get("is_verified", False)),
                    "is_available": bool(d_info.get("is_available", True)),
                    "rating": float(d_info.get("rating", 5.0)),
                    "total_completed_trips": int(d_info.get("total_completed_trips", 0))
                })
                results.append(p_copy)
        return results

    @staticmethod
    def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
        """Fetch profile by ID."""
        return DBService.get_by_id("profiles", user_id)

    @staticmethod
    def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
        """Fetch profile by email."""
        res = DBService.query("profiles", filters={"email": email.strip().lower()}, limit=1)
        return res[0] if res else None

    @staticmethod
    def authenticate_user(role_type: str, email: str, password: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Authenticate a user by role, email, and SHA-256 encrypted password.
        role_type can be 'student', 'provider' (or 'driver'), or 'admin'.
        """
        if not email or not email.strip():
            return False, "Please enter your email address.", None
        
        if not password or not password.strip():
            return False, "Please enter your password.", None

        clean_email = email.strip().lower()
        user = AuthService.get_user_by_email(clean_email)

        if not user:
            return False, f"No account found with email '{clean_email}'. Please register first.", None

        # Check account activation status
        if not user.get("is_active", True):
            return False, "Your account has been deactivated by the Campus Administrator. Please contact transport admin.", None

        # Check role alignment
        user_role = user.get("role", "")
        if role_type == "student" and user_role != Role.STUDENT.value:
            return False, f"This account is registered as '{user_role.title()}', not a Student profile.", None
        elif role_type in ("provider", "driver") and user_role not in (Role.DRIVER.value, Role.PROVIDER.value):
            return False, f"This account is registered as '{user_role.title()}', not a Service Provider.", None
        elif role_type == "admin" and user_role != Role.ADMIN.value:
            return False, f"Access denied: Admin privileges required.", None

        # Validate password using SHA-256 hash comparison
        stored_hash = user.get("password_hash") or AuthService._DYNAMIC_HASH_CACHE.get(clean_email)
        if not verify_password(password, stored_hash):
            return False, "Invalid password. Please check your credentials.", None

        # Enrich driver/provider info if applicable
        if user_role in (Role.DRIVER.value, Role.PROVIDER.value):
            driver_info = DBService.get_by_id("drivers", user["id"])
            if driver_info:
                user["business_name"] = driver_info.get("business_name") or user.get("full_name")
                user["is_verified"] = bool(driver_info.get("is_verified", False))
                user["is_available"] = bool(driver_info.get("is_available", True))
                user["rating"] = float(driver_info.get("rating", 5.0))
                user["total_completed_trips"] = int(driver_info.get("total_completed_trips", 0))

        return True, f"Welcome back, {user.get('full_name')}!", user

    @staticmethod
    def register_student(
        full_name: str,
        email: str,
        phone: str,
        program: str,
        password: str
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Register a new student with strict @gim.ac.in domain check and SHA-256 password encryption."""
        if not full_name or not full_name.strip():
            return False, "Full name is required.", None

        is_valid, msg = AuthService.validate_student_email(email)
        if not is_valid:
            return False, msg, None

        if not phone or len(phone.strip()) < 10:
            return False, "Please provide a valid 10-digit phone number.", None

        if not password or len(password.strip()) < 6:
            return False, "Password must be at least 6 characters long.", None

        clean_email = email.strip().lower()
        existing = AuthService.get_user_by_email(clean_email)
        if existing:
            return False, "An account with this GIM email already exists. Please log in.", existing

        new_id = str(uuid.uuid4())
        hashed_pw = hash_password(password)
        AuthService._DYNAMIC_HASH_CACHE[clean_email] = hashed_pw

        profile_data = {
            "id": new_id,
            "full_name": full_name.strip(),
            "email": clean_email,
            "phone": phone.strip(),
            "role": Role.STUDENT.value,
            "program": program,
            "password_hash": hashed_pw,
            "is_active": 1,
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }

        try:
            DBService.insert("profiles", profile_data)
            return True, f"Welcome to GIM Mobility, {full_name.strip()}! Registration successful.", profile_data
        except Exception as e:
            return False, f"Registration failed: {e}", None

    @staticmethod
    def register_service_provider(
        full_name: str,
        email: str,
        phone: str,
        business_name: str,
        provider_type: str,
        license_number: str,
        password: str
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Register a new Service Provider (Cab Driver or Self-Drive Agency) with SHA-256 password encryption."""
        if not full_name or not full_name.strip():
            return False, "Full name is required.", None

        if not email or "@" not in email:
            return False, "Please provide a valid email address.", None

        if not phone or len(phone.strip()) < 10:
            return False, "Please provide a valid 10-digit phone number.", None

        if not business_name or not business_name.strip():
            return False, "Business or Agency name is required.", None

        if not license_number or not license_number.strip():
            return False, "Driver license or agency registration number is required.", None

        if not password or len(password.strip()) < 6:
            return False, "Password must be at least 6 characters long.", None

        clean_email = email.strip().lower()
        existing = AuthService.get_user_by_email(clean_email)
        if existing:
            return False, "An account with this email already exists. Please log in.", existing

        new_id = str(uuid.uuid4())
        hashed_pw = hash_password(password)
        AuthService._DYNAMIC_HASH_CACHE[clean_email] = hashed_pw
        
        # Role assignment: driver for individual cab driver, provider for rental agency
        assigned_role = Role.DRIVER.value if provider_type == "individual_driver" else Role.PROVIDER.value

        profile_data = {
            "id": new_id,
            "full_name": full_name.strip(),
            "email": clean_email,
            "phone": phone.strip(),
            "role": assigned_role,
            "program": None,
            "password_hash": hashed_pw,
            "is_active": 1,
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }

        driver_data = {
            "id": new_id,
            "business_name": business_name.strip(),
            "provider_type": provider_type,
            "license_number": license_number.strip(),
            "id_proof_url": "https://gim-mobility.storage/docs/kyc_pending.pdf",
            "is_verified": 0, # Pending admin verification
            "is_available": 1,
            "rating": 5.0,
            "total_completed_trips": 0,
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }

        try:
            DBService.insert("profiles", profile_data)
            DBService.insert("drivers", driver_data)
            profile_data.update(driver_data)
            return True, f"Registration successful! Welcome {business_name.strip()}.", profile_data
        except Exception as e:
            return False, f"Registration failed: {e}", None

    @staticmethod
    def create_or_register_student(full_name: str, email: str, phone: str, program: str, password: str = DEFAULT_DEMO_PASSWORD) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Backward-compatible wrapper for student creation."""
        return AuthService.register_student(full_name, email, phone, program, password)

    @staticmethod
    def update_user_status(user_id: str, is_active: bool) -> bool:
        """Campus Admin control to suspend or activate a user account."""
        return DBService.update("profiles", user_id, {"is_active": 1 if is_active else 0})

    @staticmethod
    def init_session_state():
        """Initialize default Streamlit session state keys."""
        if "is_authenticated" not in st.session_state:
            st.session_state["is_authenticated"] = False

        if "current_role" not in st.session_state:
            st.session_state["current_role"] = Role.STUDENT.value

        if "current_user" not in st.session_state:
            st.session_state["current_user"] = None

        if "active_booking_id" not in st.session_state:
            st.session_state["active_booking_id"] = None

        if "active_tab" not in st.session_state:
            st.session_state["active_tab"] = "browse"

    @staticmethod
    def set_current_user(user: Dict[str, Any]):
        """Switch active user profile and authenticate."""
        st.session_state["current_user"] = user
        st.session_state["current_role"] = user.get("role", Role.STUDENT.value)
        st.session_state["is_authenticated"] = True

    @staticmethod
    def logout():
        """Sign out current user and return to login screen."""
        st.session_state["is_authenticated"] = False
        st.session_state["current_user"] = None
        st.session_state["active_booking_id"] = None
        st.rerun()
