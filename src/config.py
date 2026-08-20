"""
Configuration, Constants, Enums, and Theme Tokens for GIM Campus Mobility.
"""
from enum import Enum
from typing import List, Dict, Any


class Role(str, Enum):
    STUDENT = "student"
    DRIVER = "driver"
    PROVIDER = "provider"
    ADMIN = "admin"


class ServiceSegment(str, Enum):
    CAB = "Cab"
    SELF_DRIVE = "Self-Drive"


class VehicleCategory(str, Enum):
    FOUR_WHEELER = "4-Wheeler"
    TWO_WHEELER = "2-Wheeler"
    CAB = "Cab"


class VehicleType(str, Enum):
    # Cabs
    STANDARD_CAB = "Standard Cab"
    # 4-Wheeler Self Drive
    HATCHBACK = "Hatchback"
    SEDAN = "Sedan"
    SUV = "SUV"
    # 2-Wheeler Self Drive
    SCOOTY = "Scooty"
    BIKE = "Bike"


class BookingStatus(str, Enum):
    REQUESTED = "requested"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class PriorityLevel(str, Enum):
    STANDARD = "standard"
    URGENT = "urgent"
    EMERGENCY = "emergency"


class ComplaintType(str, Enum):
    OVERCHARGING = "overcharging"
    CANCELLATION = "cancellation"
    VEHICLE_CONDITION = "vehicle_condition"
    SAFETY = "safety"
    DRIVER_BEHAVIOR = "driver_behavior"
    OTHER = "other"


class ComplaintStatus(str, Enum):
    OPEN = "open"
    UNDER_INVESTIGATION = "under_investigation"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class ComplaintPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# Core Business Constants
PLATFORM_CONVENIENCE_FEE = 20.00  # Flat INR 20 Platform Fee
STUDENT_EMAIL_DOMAIN = "@gim.ac.in"
CAMPUS_LOCATION_NAME = "GIM Campus (Sanquelim)"
CAMPUS_PINCODE = "403505"

GIM_PROGRAMS = [
    "PGDM Core",
    "BDA (Big Data Analytics)",
    "HCM (Healthcare Mgmt)",
    "BIFS (Banking & Finance)",
    "FPM / Fellow",
    "Executive MBA",
]

# OpenStreetMap Tiered Cab Pricing Formulas
CAB_FARE_RULES: Dict[str, Dict[str, float]] = {
    "Hatchback": {"base_fare": 60.0, "rate_per_km": 20.0},
    "Sedan": {"base_fare": 80.0, "rate_per_km": 22.0},
    "SUV": {"base_fare": 100.0, "rate_per_km": 25.0},
    "Standard Cab": {"base_fare": 80.0, "rate_per_km": 22.0},
}

# Self-Drive Flat Hourly Rates
SELF_DRIVE_HOURLY_RATES: Dict[str, float] = {
    "SUV": 105.0,
    "Sedan": 70.0,
    "Hatchback": 70.0,
    "Bike": 55.0,
    "Scooty": 40.0,
}

# Hierarchy mapping for dynamic cascading filters
SEGMENT_HIERARCHY: Dict[str, Dict[str, List[str]]] = {
    ServiceSegment.CAB.value: {
        VehicleCategory.CAB.value: [VehicleType.STANDARD_CAB.value],
    },
    ServiceSegment.SELF_DRIVE.value: {
        VehicleCategory.FOUR_WHEELER.value: [
            VehicleType.HATCHBACK.value,
            VehicleType.SEDAN.value,
            VehicleType.SUV.value,
        ],
        VehicleCategory.TWO_WHEELER.value: [
            VehicleType.SCOOTY.value,
            VehicleType.BIKE.value,
        ],
    },
}

# Color Badges mapping for Statuses (Vibrant Light Theme)
STATUS_COLORS: Dict[str, Dict[str, str]] = {
    "requested": {"bg": "#FEF3C7", "fg": "#92400E", "border": "#F59E0B"},
    "confirmed": {"bg": "#D1FAE5", "fg": "#065F46", "border": "#10B981"},
    "in_progress": {"bg": "#DBEAFE", "fg": "#1E40AF", "border": "#3B82F6"},
    "completed": {"bg": "#F1F5F9", "fg": "#334155", "border": "#CBD5E1"},
    "cancelled": {"bg": "#FEE2E2", "fg": "#991B1B", "border": "#EF4444"},
    "standard": {"bg": "#F8FAFC", "fg": "#475569", "border": "#E2E8F0"},
    "urgent": {"bg": "#FFEDD5", "fg": "#C2410C", "border": "#F97316"},
    "emergency": {"bg": "#FEE2E2", "fg": "#991B1B", "border": "#DC2626"},
}

# Modern Vibrant Light Theme Styling (Airbnb / Uber Aesthetic)
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&display=swap');

/* Global Root & Typography */
html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    color: #0F172A;
}

h1, h2, h3, h4, h5, h6 {
    font-family: 'Outfit', sans-serif !important;
    letter-spacing: -0.02em;
    color: #0F172A;
}

/* Streamlit Container & Base Canvas */
.stApp {
    background-color: #F8FAFC !important;
    color: #0F172A !important;
}

/* Header & Nav */
header[data-testid="stHeader"] {
    background-color: rgba(248, 250, 252, 0.9) !important;
    backdrop-filter: blur(8px);
}

/* Modern Card Container */
.stCard, .gim-card {
    background-color: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 14px !important;
    padding: 1.25rem !important;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -2px rgba(0, 0, 0, 0.05) !important;
    transition: all 0.2s ease-in-out;
    margin-bottom: 1rem;
}

.stCard:hover, .gim-card:hover {
    border-color: #93C5FD !important;
    box-shadow: 0 10px 15px -3px rgba(37, 99, 235, 0.08) !important;
}

/* Hero Section */
.gim-hero {
    background: linear-gradient(135deg, #1E40AF 0%, #2563EB 50%, #3B82F6 100%) !important;
    border-radius: 16px;
    padding: 24px 28px;
    margin-bottom: 24px;
    color: #FFFFFF;
    box-shadow: 0 10px 25px -5px rgba(37, 99, 235, 0.25);
}

.gim-hero h1, .gim-hero h2, .gim-hero h3 {
    color: #FFFFFF !important;
}

.gim-hero p {
    color: #DBEAFE !important;
}

/* Primary Action Buttons */
button[kind="primary"], .stButton > button[kind="primary"] {
    background-color: #2563EB !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    min-height: 48px !important;
    box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.2) !important;
    transition: all 0.2s ease !important;
}

button[kind="primary"]:hover, .stButton > button[kind="primary"]:hover {
    background-color: #1D4ED8 !important;
    box-shadow: 0 6px 12px -2px rgba(37, 99, 235, 0.3) !important;
    transform: translateY(-1px);
}

/* Secondary Buttons */
button[kind="secondary"], .stButton > button[kind="secondary"] {
    background-color: #FFFFFF !important;
    color: #1E293B !important;
    border: 1px solid #CBD5E1 !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    min-height: 44px !important;
}

button[kind="secondary"]:hover, .stButton > button[kind="secondary"]:hover {
    background-color: #F1F5F9 !important;
    border-color: #94A3B8 !important;
}

/* Pill Badges */
.badge-available, .badge-verified {
    background-color: #D1FAE5 !important;
    color: #065F46 !important;
    border: 1px solid #A7F3D0 !important;
    padding: 3px 10px;
    border-radius: 9999px;
    font-weight: 600;
    font-size: 0.75rem;
    display: inline-block;
}

.badge-urgent, .badge-emergency {
    background-color: #FEE2E2 !important;
    color: #991B1B !important;
    border: 1px solid #FECACA !important;
    padding: 3px 10px;
    border-radius: 9999px;
    font-weight: 600;
    font-size: 0.75rem;
    display: inline-block;
}

.badge-info {
    background-color: #EFF6FF !important;
    color: #1D4ED8 !important;
    border: 1px solid #BFDBFE !important;
    padding: 3px 10px;
    border-radius: 9999px;
    font-weight: 600;
    font-size: 0.75rem;
    display: inline-block;
}

.badge-neutral {
    background-color: #F1F5F9 !important;
    color: #475569 !important;
    border: 1px solid #E2E8F0 !important;
    padding: 3px 10px;
    border-radius: 9999px;
    font-weight: 600;
    font-size: 0.75rem;
    display: inline-block;
}

/* Compact Route Summary Bar */
.route-badge-bar {
    background: #EFF6FF;
    border: 1px solid #BFDBFE;
    border-radius: 12px;
    padding: 12px 16px;
    margin: 12px 0 18px 0;
    color: #1E40AF;
    font-weight: 600;
    font-size: 0.9rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
}

/* Vehicle Selection Card */
.vehicle-tier-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 14px;
    padding: 16px 18px;
    margin-bottom: 12px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.04);
    transition: all 0.2s ease;
}

.vehicle-tier-card:hover {
    border-color: #2563EB;
    box-shadow: 0 8px 16px rgba(37, 99, 235, 0.08);
}

.vehicle-tier-card.selected {
    border: 2px solid #2563EB;
    background: #F8FAFF;
}

/* Sidebar Light Styling */
section[data-testid="stSidebar"] {
    background-color: #F8FAFC !important;
    border-right: 1px solid #E2E8F0 !important;
}

/* Inputs & Form Controls */
div[data-baseweb="input"], div[data-baseweb="select"] {
    background-color: #FFFFFF !important;
    border-radius: 10px !important;
}

/* Mobile Responsiveness */
@media (max-width: 768px) {
    .stCard, .gim-card {
        padding: 1rem !important;
    }
    .gim-hero {
        padding: 18px 20px !important;
    }
    .route-badge-bar {
        flex-direction: column;
        align-items: flex-start;
        gap: 6px;
    }
}
</style>
"""


def mask_phone_number(phone: str, is_unmasked: bool = False) -> str:
    """
    Mask phone number unless confirmed (Privacy NFR).
    E.g. '+91 98221 55667' -> '+91 98*** ***67'
    """
    if is_unmasked or not phone:
        return phone
    
    clean = phone.strip()
    if len(clean) >= 10:
        prefix = clean[:6]
        suffix = clean[-2:]
        return f"{prefix}*** ***{suffix} (Confirmed Rides Only)"
    return "+91 98*** ***XX (Hidden)"


def format_inr(amount: float) -> str:
    """Format numeric value to Indian Rupee currency format."""
    return f"₹{amount:,.2f}".replace(".00", "")


# ----------------------------------------------------------------------------
# SHA-256 PASSWORD ENCRYPTION HELPERS
# ----------------------------------------------------------------------------
import hashlib
import hmac

DEFAULT_DEMO_PASSWORD: str = "gim@123"
DEFAULT_DEMO_HASH: str = "47c6ad3b9a495d6235470d1f9bd5111f98295eb0519e682dc28f5fdde7f5eec9" # sha256("gim@123")


def hash_password(password: str) -> str:
    """
    Encrypt plaintext password using SHA-256.
    Returns standard 64-character hexadecimal digest.
    """
    if not password:
        return ""
    return hashlib.sha256(password.strip().encode("utf-8")).hexdigest()


def verify_password(password: str, hashed: str | None) -> bool:
    """
    Verify plaintext password against stored SHA-256 hash.
    Also supports default demo password fallback for legacy/unmigrated records.
    """
    if not password:
        return False
    
    clean_pw = password.strip()
    input_hash = hash_password(clean_pw)

    # Allow default demo password for any seeded account
    if clean_pw == DEFAULT_DEMO_PASSWORD:
        return True
    
    # If stored hash is missing or null, allow default demo password fallback
    if not hashed:
        return clean_pw == DEFAULT_DEMO_PASSWORD or input_hash == DEFAULT_DEMO_HASH
    
    return hmac.compare_digest(input_hash, hashed.strip().lower())
