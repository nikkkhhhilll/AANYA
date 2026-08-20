# 🌴 GIM Campus Mobility Aggregator (AANYA Mobility Engine)

A production-ready, multi-page campus mobility aggregator built for the **Goa Institute of Management (GIM)** community in Sanquelim, Goa.

Connecting students with local verified cab drivers and self-drive vehicle providers with **0% Provider Commission** and a **Flat ₹20 Convenience Fee**.

---

## 🚀 Key Features

### 1. 🎓 Student Portal
- **Domain Security Enforcement:** Strict validation allowing only `@gim.ac.in` student email addresses.
- **Segment 1: Cabs (Chauffeured Rides):**
  - Pre-negotiated transparent GIM routes (Mopa Airport, Dabolim Airport, Thivim & Karmali Stations, Panjim, Baga Beach, Mapusa).
  - Priority levels: Standard, Urgent (Flight/Exam), Emergency SOS.
  - Live availability with driver contact masking until confirmed.
- **Segment 2: Self-Drive Rentals:**
  - Dynamic cascading filters: `4-Wheeler` (Hatchback, Sedan, SUV) and `2-Wheeler` (Scooty, Bike).
  - Real-time dynamic rental pricing calculations based on hourly/daily duration.
- **₹20 UPI Convenience Fee Checkout:**
  - Dynamic UPI QR code generation and UTR/Reference ID confirmation.
  - 100% fare directly transferred to the local driver.
- **Active Ride Tracking & Reviews:**
  - Real-time phone unmasking upon booking confirmation.
  - 1–5 star rating submission and direct Grievance Ticket submission to Campus Admin.

### 2. 🚕 Driver / Provider Console
- **Live Status Toggle:** Switch between `Available (Online)` and `Off-Duty` in `< 10 seconds`.
- **Dispatch Queue:** Immediate incoming requests with urgent/emergency badges and single-click `Accept` / `Decline`.
- **Fleet Inventory Control:** Add new cabs, cars, and bikes with pricing tiers and active toggles.
- **100% Fare Retention Earnings:** Zero-commission earnings ledger.

### 3. 🛡️ Campus Admin Command Center
- **Manage Students:** Directory of registered students, program breakdowns (PGDM, BDA, HCM, BIFS), account activation/suspension.
- **Manage Drivers & KYC:** Verification queue for driver licenses, identity documents, and vendor approval/blacklisting.
- **Manage Bookings:** Full platform registry with status overrides and priority filters.
- **Manage Complaints:** Dispute resolution desk with severity levels (`Low`, `Medium`, `High`, `Critical`) and admin resolution notes.
- **Ratings & Leaderboard:** Driver performance ratings, leaderboards, and warnings for low-rated vendors (< 3.5).
- **Emergency Monitor:** High-visibility feed for urgent hospital and emergency SOS rides.
- **Interactive Analytics (Plotly):**
  - User Conversion Funnel (Drop-off flow from page view to booking completion).
  - Route Demand & Destination Popularity.
  - Fleet Segment Distribution (Cabs vs 4-Wheelers vs 2-Wheelers).
  - SLA & Latency metrics for Urgent vs Standard rides.
  - Financial KPIs: Total Platform Convenience Fees vs 100% Driver Fare Volume.

---

## 📁 Project Architecture

```text
├── .streamlit/
│   ├── config.toml             # Streamlit theme & UI styling configuration
│   └── secrets.toml            # Supabase credentials template
├── sql/
│   ├── schema.sql              # Supabase DDL (8 tables, RLS, indexes, constraints)
│   └── seed.sql                # Realistic GIM dataset
├── src/
│   ├── config.py               # Constants, Enums, CSS design tokens, phone masking
│   ├── db.py                   # Supabase singleton & resilient local engine
│   ├── services/
│   │   ├── auth_service.py     # Auth, session state, @gim.ac.in domain validation
│   │   ├── vehicle_service.py  # Dynamic cascading search, fleet & routes
│   │   ├── booking_service.py  # Concurrency lock, ₹20 UPI fee flow, transitions
│   │   ├── complaint_service.py# Grievance desk, severity, admin notes
│   │   └── analytics_service.py# Clickstream logger, funnel aggregations, financials
│   └── views/
│       ├── student_view.py     # Cabs & Self-Drive UI, ₹20 checkout, tracking
│       ├── provider_view.py    # Driver fleet & real-time dispatch queue
│       └── admin_view.py       # Campus Admin 7-tab portal & Plotly charts
├── app.py                      # Main entrypoint & role router
├── requirements.txt            # Python dependencies
└── README.md
```

---

## 🗄️ Database Setup (Supabase SQL Editor)

1. Open your [Supabase Project Dashboard](https://app.supabase.com).
2. Navigate to the **SQL Editor**.
3. Copy and run the contents of [`sql/schema.sql`](sql/schema.sql).
4. Copy and run the contents of [`sql/seed.sql`](sql/seed.sql) to populate initial data.
5. In `.streamlit/secrets.toml` or environment variables, set:
   ```toml
   SUPABASE_URL = "https://your-project-id.supabase.co"
   SUPABASE_KEY = "your-anon-or-service-role-key"
   ```

*Note: If credentials are not set, the app seamlessly runs on its built-in local engine with the identical schema and seed records.*

---

## 🏃 Running the Application

```bash
# Install dependencies
pip install -r requirements.txt

# Run Streamlit
streamlit run app.py
```
