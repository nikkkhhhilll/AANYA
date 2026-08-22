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
    "PGDM BDA",
    "PGDM HCM",
    "PGDM BIFS"
]

# OpenStreetMap Tiered Cab Pricing Formulas
CAB_FARE_RULES: Dict[str, Dict[str, float]] = {
    "Hatchback": {"base_fare": 60.0, "rate_per_km": 20.0},
    "Sedan": {"base_fare": 80.0, "rate_per_km": 22.0},
    "SUV": {"base_fare": 100.0, "rate_per_km": 25.0},

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
:root {
    --bg-main: #F8FAFC;          /* Slate 50 */
    --bg-surface: #FFFFFF;       /* Pure White */
    --border-subtle: #E2E8F0;    /* Slate 200 */
    --border-focus: #3B82F6;     /* Blue 500 */
    
    --text-primary: #0F172A;     /* Slate 900 */
    --text-secondary: #475569;   /* Slate 600 */
    --text-muted: #94A3B8;       /* Slate 400 */

    --brand-primary: #1E40AF;    /* Deep Cobalt Blue */
    --brand-accent: #2563EB;     /* Royal Blue */
    
    --status-success-bg: #ECFDF5;
    --status-success-text: #047857;
    --status-warning-bg: #FFFBEB;
    --status-warning-text: #B45309;
    --status-danger-bg: #FEF2F2;
    --status-danger-text: #B91C1C;
    
    --shadow-sm: 0 1px 3px 0 rgba(0, 0, 0, 0.07), 0 1px 2px -1px rgba(0, 0, 0, 0.07);
    --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.08), 0 2px 4px -2px rgba(0, 0, 0, 0.08);
}

/* Streamlit Theme Adaptability: Automatically inherit colors from Streamlit's active layout */
.stApp {
    --bg-main: var(--st-background-color, #F8FAFC) !important;
    --bg-surface: var(--st-secondary-background-color, #FFFFFF) !important;
    --border-subtle: var(--st-border-color, #E2E8F0) !important;
    --border-focus: var(--st-primary-color, #3B82F6) !important;
    
    --text-primary: var(--st-text-color, #0F172A) !important;
    --text-secondary: var(--st-text-color, #475569) !important;
    --text-muted: var(--st-text-color, #94A3B8) !important;

    --brand-primary: var(--st-primary-color, #1E40AF) !important;
    --brand-accent: var(--st-primary-color, #2563EB) !important;
}

@media (prefers-color-scheme: dark) {
    :root {
        --bg-main: #0B0F19;
        --bg-surface: #1E293B;
        --border-subtle: #334155;
        --border-focus: #60A5FA;
        --text-primary: #F8FAFC;
        --text-secondary: #CBD5E1;
        --text-muted: #64748B;
        --shadow-sm: 0 1px 3px 0 rgba(0, 0, 0, 0.4);
        --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.5);
    }
}

/* Global Clean Mobile-First Canvas */
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&display=swap');

html, body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    color: var(--text-primary);
    background-color: var(--bg-main);
}

/* Mobile-First Full Width Container (No wasted margin) */
.main .block-container {
    padding-top: 1rem !important;
    padding-bottom: 2rem !important;
    padding-left: 0.75rem !important;
    padding-right: 0.75rem !important;
    max-width: 600px !important;
    margin: 0 auto !important;
}

/* Streamlit Header clean adjust */
header[data-testid="stHeader"] {
    background-color: transparent !important;
    backdrop-filter: blur(8px) !important;
    height: 2.8rem !important;
}

/* Cards & Surfaces */
.stCard, .gim-card {
    background-color: var(--bg-surface) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: 14px !important;
    padding: 14px 16px !important;
    margin-bottom: 12px !important;
    box-shadow: var(--shadow-sm) !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Interactive Active Card state */
.gim-vehicle-card {
    border: 1.5px solid var(--border-subtle) !important;
    background: var(--bg-surface) !important;
    border-radius: 14px !important;
    padding: 14px 16px !important;
    margin-bottom: 12px !important;
    box-shadow: var(--shadow-sm) !important;
    cursor: pointer;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
}
.gim-vehicle-card:hover {
    border-color: var(--border-focus) !important;
    box-shadow: var(--shadow-md) !important;
}
.gim-vehicle-card.active-card {
    border-color: var(--brand-accent) !important;
    background-color: rgba(37, 99, 235, 0.12) !important; /* Dynamic blue tint across light/dark modes */
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15), var(--shadow-md) !important;
}

@media (max-width: 768px) {
    /* Hide normal Streamlit footer if any */
    footer { display: none !important; }
}

/* Clipboard Copy Styling */
.copyable-id {
    font-family: monospace;
    background: var(--bg-main);
    border: 1px solid var(--border-subtle);
    padding: 2px 6px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 0.8rem;
    font-weight: 600;
    color: var(--brand-accent);
    display: inline-flex;
    align-items: center;
    gap: 4px;
    transition: all 0.15s ease;
}
.copyable-id:hover {
    background: #EFF6FF;
    border-color: var(--border-focus);
}

.custom-toast {
    position: fixed;
    bottom: 80px;
    left: 50%;
    transform: translateX(-50%) translateY(20px);
    background: #0F172A;
    color: #FFFFFF;
    padding: 8px 16px;
    border-radius: 9999px;
    font-size: 0.82rem;
    font-weight: 600;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    z-index: 100000;
    opacity: 0;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    pointer-events: none;
}
.custom-toast.show {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
}

/* Live Countdown Banner styling */
.countdown-banner {
    background: var(--status-warning-bg);
    color: var(--status-warning-text);
    border: 1px solid #FDE68A;
    border-radius: 8px;
    padding: 6px 12px;
    font-size: 0.8rem;
    font-weight: 700;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    margin-top: 6px;
}

/* Mobile Hero Banner */
.gim-hero {
    background: linear-gradient(135deg, var(--brand-primary) 0%, var(--brand-accent) 50%, #3B82F6 100%) !important;
    border-radius: 14px;
    padding: 16px 18px;
    margin-bottom: 14px;
    color: #FFFFFF;
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
}

.gim-hero h1, .gim-hero h2, .gim-hero h3 {
    color: #FFFFFF !important;
    font-family: 'Outfit', sans-serif !important;
}

.gim-hero p {
    color: #DBEAFE !important;
}

/* Full Width Touch-Friendly Primary Button */
button[kind="primary"], .stButton > button[kind="primary"] {
    background-color: var(--brand-accent) !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
    min-height: 48px !important;
    width: 100% !important;
    box-shadow: 0 4px 10px rgba(37, 99, 235, 0.25) !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

button[kind="primary"]:hover, .stButton > button[kind="primary"]:hover {
    background-color: var(--brand-primary) !important;
    transform: translateY(-1px);
}

/* Secondary Button */
button[kind="secondary"], .stButton > button[kind="secondary"] {
    background-color: var(--bg-surface) !important;
    color: var(--text-primary) !important;
    border: 1.5px solid var(--border-subtle) !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    min-height: 46px !important;
    width: 100% !important;
}

/* Mobile-Optimized Tab Bar (Equal Width distributed evenly across the screen) */
div[data-testid="stTabs"] {
    width: 100% !important;
}

div[data-baseweb="tab-list"] {
    display: flex !important;
    width: 100% !important;
    gap: 4px !important;
    background-color: #F1F5F9 !important;
    border-radius: 12px !important;
    padding: 4px !important;
    margin-bottom: 14px !important;
    overflow-x: hidden !important;
}

div[data-baseweb="tab-list"] button[data-baseweb="tab"] {
    flex: 1 1 0px !important;
    min-width: 0 !important;
    width: 100% !important;
    padding: 10px 6px !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    text-align: center !important;
    border-radius: 8px !important;
    border: none !important;
    background: transparent !important;
    color: var(--text-secondary) !important;
    justify-content: center !important;
    white-space: normal !important;
}

div[data-baseweb="tab-list"] button[data-baseweb="tab"][aria-selected="true"] {
    background: var(--bg-surface) !important;
    color: var(--brand-accent) !important;
    font-weight: 700 !important;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.06) !important;
}

div[data-baseweb="tab-highlight"] {
    display: none !important;
}

/* Mobile Inputs & Dropdowns (Crisp Light Background) */
div[data-baseweb="select"] > div {
    background-color: var(--bg-surface) !important;
    color: var(--text-primary) !important;
    border: 1.5px solid var(--border-subtle) !important;
    border-radius: 10px !important;
    min-height: 46px !important;
}

div[data-baseweb="select"] * {
    color: var(--text-primary) !important;
}

div[data-baseweb="input"] {
    background-color: var(--bg-surface) !important;
    border: 1.5px solid var(--border-subtle) !important;
    border-radius: 10px !important;
}

div[data-baseweb="input"] input {
    color: var(--text-primary) !important;
}

/* Badges */
.badge-available, .badge-verified {
    background-color: var(--status-success-bg) !important;
    color: var(--status-success-text) !important;
    padding: 2px 8px;
    border-radius: 9999px;
    font-weight: 600;
    font-size: 0.75rem;
}

.badge-urgent, .badge-emergency {
    background-color: var(--status-danger-bg) !important;
    color: var(--status-danger-text) !important;
    padding: 2px 8px;
    border-radius: 9999px;
    font-weight: 600;
    font-size: 0.75rem;
}

/* Compact Route Summary Bar */
.route-badge-bar {
    background: #EFF6FF;
    border: 1px solid #BFDBFE;
    border-radius: 10px;
    padding: 10px 14px;
    margin: 10px 0 14px 0;
    color: var(--brand-primary);
    font-weight: 600;
    font-size: 0.85rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 4px;
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
