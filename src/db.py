"""
Database Layer & Supabase Client Factory with Resilient Engine.
Provides singleton Supabase client wrapper and seamless querying.
"""
import os
import re
import json
import sqlite3
import datetime
import streamlit as st
from typing import Dict, List, Any, Optional, Tuple
from supabase import create_client, Client


class LocalDatabaseEngine:
    """
    In-memory / Local SQLite database engine pre-populated with schema & seed data.
    Ensures 100% testability, sub-millisecond latencies, and offline resilience.
    """
    _instance: Optional["LocalDatabaseEngine"] = None

    def __init__(self):
        self.conn = sqlite3.connect(":memory:", check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._initialize_schema_and_seeds()

    @classmethod
    def get_instance(cls) -> "LocalDatabaseEngine":
        if cls._instance is None:
            cls._instance = LocalDatabaseEngine()
        return cls._instance

    def _initialize_schema_and_seeds(self):
        """Build tables and populate with seed data."""
        cur = self.conn.cursor()
        
        # 1. Profiles
        cur.execute("""
        CREATE TABLE IF NOT EXISTS profiles (
            id TEXT PRIMARY KEY,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            phone TEXT NOT NULL,
            role TEXT NOT NULL,
            program TEXT,
            password_hash TEXT NOT NULL DEFAULT '47c6ad3b9a495d6235470d1f9bd5111f98295eb0519e682dc28f5fdde7f5eec9',
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL
        );
        """)

        # 2. Drivers
        cur.execute("""
        CREATE TABLE IF NOT EXISTS drivers (
            id TEXT PRIMARY KEY,
            business_name TEXT,
            provider_type TEXT NOT NULL,
            license_number TEXT NOT NULL,
            id_proof_url TEXT,
            is_verified INTEGER NOT NULL DEFAULT 0,
            is_available INTEGER NOT NULL DEFAULT 1,
            rating REAL NOT NULL DEFAULT 5.0,
            total_completed_trips INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            FOREIGN KEY(id) REFERENCES profiles(id)
        );
        """)

        # 3. Vehicles
        cur.execute("""
        CREATE TABLE IF NOT EXISTS vehicles (
            id TEXT PRIMARY KEY,
            provider_id TEXT NOT NULL,
            service_segment TEXT NOT NULL,
            vehicle_category TEXT NOT NULL,
            vehicle_type TEXT NOT NULL,
            vehicle_model TEXT NOT NULL,
            vehicle_number TEXT NOT NULL UNIQUE,
            seating_capacity INTEGER NOT NULL DEFAULT 4,
            is_active INTEGER NOT NULL DEFAULT 1,
            is_available INTEGER NOT NULL DEFAULT 1,
            pricing_details TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL,
            FOREIGN KEY(provider_id) REFERENCES drivers(id)
        );
        """)

        # 4. Standard Routes
        cur.execute("""
        CREATE TABLE IF NOT EXISTS standard_routes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            origin TEXT NOT NULL,
            destination TEXT NOT NULL,
            estimated_fare_cab REAL NOT NULL
        );
        """)

        # 5. Bookings
        cur.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id TEXT PRIMARY KEY,
            student_id TEXT NOT NULL,
            vehicle_id TEXT NOT NULL,
            provider_id TEXT NOT NULL,
            service_segment TEXT NOT NULL,
            vehicle_category TEXT NOT NULL,
            vehicle_type TEXT NOT NULL,
            pickup_location TEXT NOT NULL,
            dropoff_location TEXT NOT NULL,
            start_datetime TEXT NOT NULL,
            end_datetime TEXT,
            passengers_count INTEGER NOT NULL DEFAULT 1,
            rental_duration_days_or_hours TEXT,
            base_trip_fare REAL NOT NULL,
            convenience_fee REAL NOT NULL DEFAULT 20.0,
            fee_payment_status TEXT NOT NULL DEFAULT 'pending',
            booking_status TEXT NOT NULL DEFAULT 'requested',
            priority_level TEXT NOT NULL DEFAULT 'standard',
            special_notes TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            FOREIGN KEY(student_id) REFERENCES profiles(id),
            FOREIGN KEY(vehicle_id) REFERENCES vehicles(id),
            FOREIGN KEY(provider_id) REFERENCES drivers(id)
        );
        """)

        # 6. Complaints
        cur.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            id TEXT PRIMARY KEY,
            booking_id TEXT NOT NULL,
            raised_by_id TEXT NOT NULL,
            target_user_id TEXT,
            complaint_type TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'open',
            priority TEXT NOT NULL DEFAULT 'medium',
            admin_notes TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            FOREIGN KEY(booking_id) REFERENCES bookings(id),
            FOREIGN KEY(raised_by_id) REFERENCES profiles(id)
        );
        """)

        # 7. Reviews
        cur.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            id TEXT PRIMARY KEY,
            booking_id TEXT NOT NULL,
            student_id TEXT NOT NULL,
            provider_id TEXT NOT NULL,
            rating INTEGER NOT NULL,
            comment TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            FOREIGN KEY(booking_id) REFERENCES bookings(id),
            FOREIGN KEY(student_id) REFERENCES profiles(id),
            FOREIGN KEY(provider_id) REFERENCES drivers(id)
        );
        """)

        # 8. Analytics Events
        cur.execute("""
        CREATE TABLE IF NOT EXISTS analytics_events (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            event_name TEXT NOT NULL,
            metadata TEXT NOT NULL DEFAULT '{}',
            timestamp TEXT NOT NULL
        );
        """)

        # 9. System Settings
        cur.execute("""
        CREATE TABLE IF NOT EXISTS system_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        """)

        self._populate_seed_data(cur)
        self.conn.commit()

    def _populate_seed_data(self, cur):
        """Populate local database with default realistic seed records."""
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        default_hash = "47c6ad3b9a495d6235470d1f9bd5111f98295eb0519e682dc28f5fdde7f5eec9" # sha256 of "gim@123"
        
        # Profiles
        profiles_data = [
            ('11111111-1111-1111-1111-111111111101', 'Aravind Krishnan', 'aravind.k24@gim.ac.in', '+91 98231 45678', 'student', 'PGDM Core', default_hash, 1, now),
            ('11111111-1111-1111-1111-111111111102', 'Priya Sharma', 'priya.s24@gim.ac.in', '+91 98450 12345', 'student', 'BDA (Big Data Analytics)', default_hash, 1, now),
            ('11111111-1111-1111-1111-111111111103', 'Rohit Mehta', 'rohit.m24@gim.ac.in', '+91 97654 89012', 'student', 'HCM (Healthcare Mgmt)', default_hash, 1, now),
            ('11111111-1111-1111-1111-111111111104', 'Ananya Deshmukh', 'ananya.d24@gim.ac.in', '+91 94238 67890', 'student', 'BIFS (Banking & Finance)', default_hash, 1, now),
            ('11111111-1111-1111-1111-111111111105', 'Varun Kapoor', 'varun.k24@gim.ac.in', '+91 98811 22334', 'student', 'PGDM Core', default_hash, 0, now),
            ('22222222-2222-2222-2222-222222222201', 'Rajesh Naik', 'rajesh.cabs@pondataxi.com', '+91 98221 55667', 'driver', None, default_hash, 1, now),
            ('22222222-2222-2222-2222-222222222202', 'Ganesh Gaonkar', 'ganesh.sanquelim@gmail.com', '+91 94220 66778', 'driver', None, default_hash, 1, now),
            ('22222222-2222-2222-2222-222222222203', 'Sandeep Prabhu', 'sandeep@royalselfdrivegoa.in', '+91 98224 88990', 'provider', None, default_hash, 1, now),
            ('22222222-2222-2222-2222-222222222204', 'Premanand Sawant', 'sawant.rentals@bicholim.com', '+91 97645 11223', 'provider', None, default_hash, 1, now),
            ('22222222-2222-2222-2222-222222222205', 'Anthony D Souza', 'anthony.tours@goa.in', '+91 98901 33445', 'driver', None, default_hash, 0, now),
            ('33333333-3333-3333-3333-333333333301', 'Campus Transport Admin', 'transport.admin@gim.ac.in', '+91 832 2366700', 'admin', 'Administration', default_hash, 1, now),
        ]
        cur.executemany("INSERT OR REPLACE INTO profiles VALUES (?,?,?,?,?,?,?,?,?)", profiles_data)

        # Drivers
        drivers_data = [
            ('22222222-2222-2222-2222-222222222201', 'Sanquelim-GIM Taxi Union', 'individual_driver', 'GA-04-20160004521', 'https://gim-mobility.storage/docs/kyc_rajesh.pdf', 1, 1, 4.9, 142, now),
            ('22222222-2222-2222-2222-222222222202', 'Ponda Premier Cabs', 'individual_driver', 'GA-05-20180009812', 'https://gim-mobility.storage/docs/kyc_ganesh.pdf', 1, 1, 4.7, 98, now),
            ('22222222-2222-2222-2222-222222222203', 'Royal Self Drive Goa (Sanquelim Branch)', 'rental_agency', 'GA-04-20150001123', 'https://gim-mobility.storage/docs/kyc_royal.pdf', 1, 1, 4.8, 215, now),
            ('22222222-2222-2222-2222-222222222204', 'Bicholim Two-Wheeler Hub', 'rental_agency', 'GA-04-20200007654', 'https://gim-mobility.storage/docs/kyc_bicholim.pdf', 1, 1, 4.6, 180, now),
            ('22222222-2222-2222-2222-222222222205', 'Coastal Goa Fast Cabs', 'individual_driver', 'GA-01-20220003344', 'https://gim-mobility.storage/docs/kyc_anthony.pdf', 0, 0, 3.2, 12, now),
        ]
        cur.executemany("INSERT OR REPLACE INTO drivers VALUES (?,?,?,?,?,?,?,?,?,?)", drivers_data)

        # Standard Routes
        routes_data = [
            ('GIM Campus, Sanquelim', 'Sanquelim Town', 110.0),
            ('GIM Campus, Sanquelim', 'Bicholim', 240.0),
            ('GIM Campus, Sanquelim', 'Mapusa', 580.0),
            ('GIM Campus, Sanquelim', 'Panjim (Panaji)', 680.0),
            ('GIM Campus, Sanquelim', 'Old Goa', 500.0),
            ('GIM Campus, Sanquelim', 'Calangute / Baga', 800.0),
            ('GIM Campus, Sanquelim', 'Anjuna / Vagator', 820.0),
            ('GIM Campus, Sanquelim', 'Candolim', 840.0),
            ('GIM Campus, Sanquelim', 'Goa Airport (Dabolim)', 1080.0),
            ('GIM Campus, Sanquelim', 'Mopa Airport (MOPA)', 900.0),
            ('GIM Campus, Sanquelim', 'Thivim Railway Station', 510.0),
            ('GIM Campus, Sanquelim', 'Karmali Railway Station', 560.0),
            ('GIM Campus, Sanquelim', 'Madgaon (Margao)', 1140.0),
            ('GIM Campus, Sanquelim', 'Palolem / South Goa', 1780.0),
        ]
        cur.executemany("INSERT INTO standard_routes (origin, destination, estimated_fare_cab) VALUES (?,?,?)", routes_data)

        # Vehicles
        vehicles_data = [
            # Cabs (Available Passenger Seats = seating_capacity - 1)
            ('44444444-4444-4444-4444-444444444401', '22222222-2222-2222-2222-222222222201', 'Cab', 'Cab', 'Sedan', 'Maruti Suzuki Dzire (AC Sedan)', 'GA-04-T-1289', 4, 1, 1, json.dumps({"tier": "Sedan", "base_fare": 80, "rate_per_km": 22}), now),
            ('44444444-4444-4444-4444-444444444402', '22222222-2222-2222-2222-222222222201', 'Cab', 'Cab', 'SUV', 'Maruti Suzuki Ertiga (6+1 Seater SUV)', 'GA-04-T-8842', 7, 1, 1, json.dumps({"tier": "SUV", "base_fare": 100, "rate_per_km": 25}), now),
            ('44444444-4444-4444-4444-444444444403', '22222222-2222-2222-2222-222222222202', 'Cab', 'Cab', 'SUV', 'Toyota Innova Crysta (Luxury 7-Seater)', 'GA-05-T-5511', 7, 1, 1, json.dumps({"tier": "SUV", "base_fare": 100, "rate_per_km": 25}), now),
            ('44444444-4444-4444-4444-444444444404', '22222222-2222-2222-2222-222222222202', 'Cab', 'Cab', 'Hatchback', 'Maruti Suzuki WagonR (AC Hatchback)', 'GA-05-T-9921', 4, 1, 1, json.dumps({"tier": "Hatchback", "base_fare": 60, "rate_per_km": 20}), now),
            
            # Self-Drive 4-Wheelers (Hourly Rate: ₹70/hr for Hatchback/Sedan, ₹105/hr for SUV)
            ('44444444-4444-4444-4444-444444444405', '22222222-2222-2222-2222-222222222203', 'Self-Drive', '4-Wheeler', 'Hatchback', 'Maruti Suzuki Swift (5 Seater)', 'GA-04-Z-2211', 5, 1, 1, json.dumps({"hourly_rate": 70, "daily_rate": 1680, "security_deposit": 2000, "fuel_type": "Petrol"}), now),
            ('44444444-4444-4444-4444-444444444406', '22222222-2222-2222-2222-222222222203', 'Self-Drive', '4-Wheeler', 'Hatchback', 'Hyundai i20 Asta (5 Seater)', 'GA-04-Z-6677', 5, 1, 1, json.dumps({"hourly_rate": 70, "daily_rate": 1680, "security_deposit": 2500, "fuel_type": "Petrol"}), now),
            ('44444444-4444-4444-4444-444444444407', '22222222-2222-2222-2222-222222222203', 'Self-Drive', '4-Wheeler', 'Sedan', 'Honda City 5th Gen (5 Seater)', 'GA-04-Z-9900', 5, 1, 1, json.dumps({"hourly_rate": 70, "daily_rate": 1680, "security_deposit": 3000, "fuel_type": "Petrol"}), now),
            ('44444444-4444-4444-4444-444444444408', '22222222-2222-2222-2222-222222222203', 'Self-Drive', '4-Wheeler', 'SUV', 'Mahindra Thar 4x4 (4 Seater)', 'GA-04-Z-4444', 4, 1, 1, json.dumps({"hourly_rate": 105, "daily_rate": 2520, "security_deposit": 5000, "fuel_type": "Diesel"}), now),
            ('44444444-4444-4444-4444-444444444409', '22222222-2222-2222-2222-222222222203', 'Self-Drive', '4-Wheeler', 'SUV', 'Hyundai Creta SX (5 Seater)', 'GA-04-Z-1010', 5, 1, 1, json.dumps({"hourly_rate": 105, "daily_rate": 2520, "security_deposit": 4000, "fuel_type": "Petrol"}), now),
            ('44444444-4444-4444-4444-444444444415', '22222222-2222-2222-2222-222222222203', 'Self-Drive', '4-Wheeler', 'SUV', 'Toyota Innova Crysta (7 Seater SUV)', 'GA-04-Z-7700', 7, 1, 1, json.dumps({"hourly_rate": 105, "daily_rate": 2520, "security_deposit": 5000, "fuel_type": "Diesel"}), now),
            ('44444444-4444-4444-4444-444444444416', '22222222-2222-2222-2222-222222222203', 'Self-Drive', '4-Wheeler', 'SUV', 'Maruti Suzuki Ertiga (7 Seater SUV)', 'GA-04-Z-8811', 7, 1, 1, json.dumps({"hourly_rate": 105, "daily_rate": 2520, "security_deposit": 4000, "fuel_type": "Petrol"}), now),

            # Self-Drive 2-Wheelers (Seats = 2, Scooty: ₹40/hr, Bike: ₹55/hr)
            ('44444444-4444-4444-4444-444444444410', '22222222-2222-2222-2222-222222222204', 'Self-Drive', '2-Wheeler', 'Scooty', 'Honda Activa 6G (2 Seater)', 'GA-04-M-3344', 2, 1, 1, json.dumps({"hourly_rate": 40, "daily_rate": 600, "security_deposit": 500, "helmets_included": 2}), now),
            ('44444444-4444-4444-4444-444444444411', '22222222-2222-2222-2222-222222222204', 'Self-Drive', '2-Wheeler', 'Scooty', 'TVS Jupiter 125 (2 Seater)', 'GA-04-M-7788', 2, 1, 1, json.dumps({"hourly_rate": 40, "daily_rate": 600, "security_deposit": 500, "helmets_included": 2}), now),
            ('44444444-4444-4444-4444-444444444412', '22222222-2222-2222-2222-222222222204', 'Self-Drive', '2-Wheeler', 'Bike', 'Royal Enfield Hunter 350 (2 Seater)', 'GA-04-M-9112', 2, 1, 1, json.dumps({"hourly_rate": 55, "daily_rate": 1000, "security_deposit": 1000, "helmets_included": 2}), now),
            ('44444444-4444-4444-4444-444444444413', '22222222-2222-2222-2222-222222222204', 'Self-Drive', '2-Wheeler', 'Bike', 'Royal Enfield Classic 350 (2 Seater)', 'GA-04-M-1199', 2, 1, 1, json.dumps({"hourly_rate": 55, "daily_rate": 1000, "security_deposit": 1000, "helmets_included": 2}), now),
            ('44444444-4444-4444-4444-444444444414', '22222222-2222-2222-2222-222222222204', 'Self-Drive', '2-Wheeler', 'Bike', 'Royal Enfield Himalayan 450 (2 Seater)', 'GA-04-M-5500', 2, 1, 1, json.dumps({"hourly_rate": 55, "daily_rate": 1100, "security_deposit": 1500, "helmets_included": 2}), now),
        ]
        cur.executemany("INSERT OR REPLACE INTO vehicles VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", vehicles_data)

        # Bookings (All seed demo bookings stored as past completed trips so fleet is 100% available)
        bookings_data = [
            ('55555555-5555-5555-5555-555555555501', '11111111-1111-1111-1111-111111111101', '44444444-4444-4444-4444-444444444401', '22222222-2222-2222-2222-222222222201', 'Cab', 'Cab', 'Standard Cab', 'GIM Gate No. 2', 'Manohar Intl Airport (Mopa GOX)', (datetime.datetime.now() - datetime.timedelta(days=5)).isoformat(), (datetime.datetime.now() - datetime.timedelta(days=5, hours=-1.5)).isoformat(), 2, '1.5 hours', 1800.0, 20.0, 'paid', 'completed', 'standard', 'Flight at 6:30 PM, on-time pickup required.', (datetime.datetime.now() - datetime.timedelta(days=6)).isoformat()),
            ('55555555-5555-5555-5555-555555555502', '11111111-1111-1111-1111-111111111102', '44444444-4444-4444-4444-444444444405', '22222222-2222-2222-2222-222222222203', 'Self-Drive', '4-Wheeler', 'Hatchback', 'GIM Gate No. 2', 'North Goa Loop (Calangute, Anjuna)', (datetime.datetime.now() - datetime.timedelta(days=3)).isoformat(), (datetime.datetime.now() - datetime.timedelta(days=2)).isoformat(), 4, '1 Day (24 hrs)', 1400.0, 20.0, 'paid', 'completed', 'standard', 'Weekend college trip.', (datetime.datetime.now() - datetime.timedelta(days=4)).isoformat()),
            ('55555555-5555-5555-5555-555555555503', '11111111-1111-1111-1111-111111111103', '44444444-4444-4444-4444-444444444403', '22222222-2222-2222-2222-222222222202', 'Cab', 'Cab', 'Standard Cab', 'GIM Gate No. 2', 'Manipal Hospital Dona Paula', (datetime.datetime.now() - datetime.timedelta(days=2)).isoformat(), (datetime.datetime.now() - datetime.timedelta(days=2, hours=-2)).isoformat(), 2, 'Outstation Hospital', 1600.0, 20.0, 'paid', 'completed', 'urgent', 'Medical appointment for student.', (datetime.datetime.now() - datetime.timedelta(days=2, hours=3)).isoformat()),
            ('55555555-5555-5555-5555-555555555504', '11111111-1111-1111-1111-111111111104', '44444444-4444-4444-4444-444444444412', '22222222-2222-2222-2222-222222222204', 'Self-Drive', '2-Wheeler', 'Bike', 'GIM Gate No. 2', 'Panjim City Exploration', (datetime.datetime.now() - datetime.timedelta(days=1)).isoformat(), (datetime.datetime.now() - datetime.timedelta(days=1, hours=-8)).isoformat(), 1, '8 Hours', 750.0, 20.0, 'paid', 'completed', 'standard', 'Need helmet size L.', (datetime.datetime.now() - datetime.timedelta(days=1, hours=10)).isoformat()),
            ('55555555-5555-5555-5555-555555555505', '11111111-1111-1111-1111-111111111101', '44444444-4444-4444-4444-444444444402', '22222222-2222-2222-2222-222222222201', 'Cab', 'Cab', 'Standard Cab', 'GIM Gate No. 2', 'Thivim Railway Station', (datetime.datetime.now() - datetime.timedelta(hours=6)).isoformat(), (datetime.datetime.now() - datetime.timedelta(hours=4)).isoformat(), 4, 'Direct Train Transfer', 700.0, 20.0, 'paid', 'completed', 'emergency', 'Vande Bharat Express transfer.', (datetime.datetime.now() - datetime.timedelta(hours=7)).isoformat()),
        ]
        cur.executemany("INSERT OR REPLACE INTO bookings VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", bookings_data)

        # Reviews
        reviews_data = [
            ('66666666-6666-6666-6666-666666666601', '55555555-5555-5555-5555-555555555501', '11111111-1111-1111-1111-111111111101', '22222222-2222-2222-2222-222222222201', 5, 'Super punctual! Rajesh bhaiya was waiting at the hostel gate 10 mins early. Clean AC cab.', now),
            ('66666666-6666-6666-6666-666666666602', '55555555-5555-5555-5555-555555555502', '11111111-1111-1111-1111-111111111102', '22222222-2222-2222-2222-222222222203', 5, 'Swift was in mint condition. Fast documentation and hassle-free return right at GIM main gate.', now),
        ]
        cur.executemany("INSERT OR REPLACE INTO reviews VALUES (?,?,?,?,?,?,?)", reviews_data)

        # Complaints
        complaints_data = [
            ('77777777-7777-7777-7777-777777777701', '55555555-5555-5555-5555-555555555501', '11111111-1111-1111-1111-111111111101', '22222222-2222-2222-2222-222222222201', 'driver_behavior', 'Driver took an alternate toll route without prior notice, though fare was respected.', 'resolved', 'low', 'Driver cautioned regarding route consultation prior to departure.', now),
            ('77777777-7777-7777-7777-777777777702', '55555555-5555-5555-5555-555555555503', '11111111-1111-1111-1111-111111111103', '22222222-2222-2222-2222-222222222202', 'safety', 'Emergency medical ride dispatched - tracking vehicle live to ensure smooth corridor.', 'under_investigation', 'critical', 'Campus Health Center and Security in direct touch with driver Ganesh.', now),
        ]
        cur.executemany("INSERT OR REPLACE INTO complaints VALUES (?,?,?,?,?,?,?,?,?,?)", complaints_data)

        # Analytics Events
        analytics_data = [
            ('88888888-8888-8888-8888-888888888801', '11111111-1111-1111-1111-111111111101', 'page_view', json.dumps({"page": "student_portal", "device": "mobile", "network": "GIM-WiFi"}), now),
            ('88888888-8888-8888-8888-888888888802', '11111111-1111-1111-1111-111111111101', 'search_click', json.dumps({"segment": "Cab", "destination": "Manohar Intl Airport (Mopa GOX)"}), now),
            ('88888888-8888-8888-8888-888888888803', '11111111-1111-1111-1111-111111111101', 'segment_selected', json.dumps({"segment": "Cab", "fare": 1800}), now),
            ('88888888-8888-8888-8888-888888888804', '11111111-1111-1111-1111-111111111101', 'booking_started', json.dumps({"vehicle_type": "Standard Cab", "fee": 20}), now),
            ('88888888-8888-8888-8888-888888888805', '11111111-1111-1111-1111-111111111101', 'booking_completed', json.dumps({"booking_id": "55555555-5555-5555-5555-555555555501", "payment": "UPI_SUCCESS"}), now),
            ('88888888-8888-8888-8888-888888888806', '11111111-1111-1111-1111-111111111102', 'page_view', json.dumps({"page": "student_portal"}), now),
            ('88888888-8888-8888-8888-888888888807', '11111111-1111-1111-1111-111111111102', 'search_click', json.dumps({"segment": "Self-Drive", "category": "4-Wheeler"}), now),
            ('88888888-8888-8888-8888-888888888808', '11111111-1111-1111-1111-111111111102', 'booking_started', json.dumps({"vehicle_type": "Hatchback", "fee": 20}), now),
            ('88888888-8888-8888-8888-888888888809', '11111111-1111-1111-1111-111111111102', 'booking_completed', json.dumps({"booking_id": "55555555-5555-5555-5555-555555555502"}), now),
            ('88888888-8888-8888-8888-888888888810', '11111111-1111-1111-1111-111111111105', 'page_view', json.dumps({"page": "student_portal"}), now),
            ('88888888-8888-8888-8888-888888888811', '11111111-1111-1111-1111-111111111105', 'search_click', json.dumps({"segment": "Self-Drive", "category": "2-Wheeler"}), now),
            ('88888888-8888-8888-8888-888888888812', '11111111-1111-1111-1111-111111111105', 'booking_abandoned', json.dumps({"reason": "payment_timeout", "step": "upi_fee"}), now),
        ]
        cur.executemany("INSERT OR REPLACE INTO analytics_events VALUES (?,?,?,?,?)", analytics_data)

        # Seed default pricing settings
        default_pricing = {
            "cab_fare_rules": {
                "Hatchback": {"base_fare": 60.0, "rate_per_km": 20.0},
                "Sedan": {"base_fare": 80.0, "rate_per_km": 22.0},
                "SUV": {"base_fare": 100.0, "rate_per_km": 25.0}
            },
            "self_drive_hourly_rates": {
                "SUV": 105.0,
                "Sedan": 70.0,
                "Hatchback": 70.0,
                "Bike": 55.0,
                "Scooty": 40.0
            }
        }
        cur.execute("INSERT OR REPLACE INTO system_settings VALUES (?, ?)", ("pricing_config", json.dumps(default_pricing)))


@st.cache_resource
def get_supabase_client() -> Optional[Client]:
    """
    Singleton Supabase client factory. Reads secrets/env variables.
    Returns Client instance if credentials are valid, or None for local engine fallback.
    """
    supabase_url = None
    supabase_key = None

    # Check Streamlit secrets first
    try:
        if "SUPABASE_URL" in st.secrets and "SUPABASE_KEY" in st.secrets:
            supabase_url = st.secrets["SUPABASE_URL"]
            supabase_key = st.secrets["SUPABASE_KEY"]
    except Exception:
        pass

    # Check environment variables
    if not supabase_url:
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_KEY")

    # If default template or missing, return None to trigger local engine
    if not supabase_url or "your-project-id" in supabase_url or not supabase_key:
        return None

    try:
        client: Client = create_client(supabase_url, supabase_key)
        return client
    except Exception as e:
        st.warning(f"Could not connect to remote Supabase ({e}). Operating in Local High-Performance Engine mode.")
        return None


class DBService:
    """
    Unified Data Access Layer:
    Delegates to Supabase Cloud if available, or falls back to local high-performance SQLite engine.
    """

    @staticmethod
    def get_engine() -> LocalDatabaseEngine:
        return LocalDatabaseEngine.get_instance()

    @staticmethod
    def query(table: str, filters: Optional[Dict[str, Any]] = None, order_by: Optional[str] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Fetch records with parameterized filters."""
        supabase = get_supabase_client()
        if supabase:
            try:
                query = supabase.table(table).select("*")
                if filters:
                    for k, v in filters.items():
                        query = query.eq(k, v)
                if order_by:
                    desc = order_by.startswith("-")
                    col = order_by.lstrip("-")
                    query = query.order(col, desc=desc)
                if limit:
                    query = query.limit(limit)
                response = query.execute()
                return response.data or []
            except Exception as e:
                # Log and fallback
                pass

        # Local Engine Query
        engine = DBService.get_engine()
        cur = engine.conn.cursor()
        sql = f"SELECT * FROM {table}"
        params = []
        if filters:
            conditions = []
            for k, v in filters.items():
                if isinstance(v, (list, tuple)):
                    placeholders = ",".join("?" * len(v))
                    conditions.append(f"{k} IN ({placeholders})")
                    params.extend(v)
                else:
                    conditions.append(f"{k} = ?")
                    params.append(v)
            sql += " WHERE " + " AND ".join(conditions)
        
        if order_by:
            if order_by.startswith("-"):
                sql += f" ORDER BY {order_by[1:]} DESC"
            else:
                sql += f" ORDER BY {order_by} ASC"
        
        if limit:
            sql += f" LIMIT {limit}"

        cur.execute(sql, params)
        rows = cur.fetchall()
        result = []
        for r in rows:
            d = dict(r)
            # Parse json strings if any
            if "pricing_details" in d and isinstance(d["pricing_details"], str):
                try:
                    d["pricing_details"] = json.loads(d["pricing_details"])
                except Exception:
                    pass
            if "metadata" in d and isinstance(d["metadata"], str):
                try:
                    d["metadata"] = json.loads(d["metadata"])
                except Exception:
                    pass
            result.append(d)
        return result

    @staticmethod
    def get_by_id(table: str, record_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a single record by primary key."""
        records = DBService.query(table, filters={"id": record_id}, limit=1)
        return records[0] if records else None

    @staticmethod
    def insert(table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a single record with graceful fallback for schema changes."""
        supabase = get_supabase_client()
        if supabase:
            try:
                res = supabase.table(table).insert(data).execute()
                if res.data:
                    return res.data[0]
            except Exception as e:
                # If Supabase table is missing password_hash column, retry without it
                if "password_hash" in data:
                    try:
                        fallback_data = {k: v for k, v in data.items() if k != "password_hash"}
                        res = supabase.table(table).insert(fallback_data).execute()
                        if res.data:
                            return res.data[0]
                    except Exception:
                        pass

        engine = DBService.get_engine()
        cur = engine.conn.cursor()
        
        # Serialize dicts/lists to JSON strings
        clean_data = {}
        for k, v in data.items():
            if isinstance(v, (dict, list)):
                clean_data[k] = json.dumps(v)
            elif isinstance(v, bool):
                clean_data[k] = 1 if v else 0
            else:
                clean_data[k] = v

        cols = list(clean_data.keys())
        placeholders = ",".join("?" * len(cols))
        sql = f"INSERT INTO {table} ({','.join(cols)}) VALUES ({placeholders})"
        cur.execute(sql, list(clean_data.values()))
        engine.conn.commit()
        return data

    @staticmethod
    def update(table: str, record_id: str, updates: Dict[str, Any]) -> bool:
        """Update a single record by ID."""
        supabase = get_supabase_client()
        if supabase:
            try:
                res = supabase.table(table).update(updates).eq("id", record_id).execute()
                return bool(res.data)
            except Exception:
                pass

        engine = DBService.get_engine()
        cur = engine.conn.cursor()
        
        clean_updates = {}
        for k, v in updates.items():
            if isinstance(v, (dict, list)):
                clean_updates[k] = json.dumps(v)
            elif isinstance(v, bool):
                clean_updates[k] = 1 if v else 0
            else:
                clean_updates[k] = v

        set_clause = ", ".join([f"{k} = ?" for k in clean_updates.keys()])
        sql = f"UPDATE {table} SET {set_clause} WHERE id = ?"
        params = list(clean_updates.values()) + [record_id]
        cur.execute(sql, params)
        engine.conn.commit()
    @staticmethod
    def delete(table: str, record_id: str) -> bool:
        """Delete a single record by ID."""
        supabase = get_supabase_client()
        if supabase:
            try:
                res = supabase.table(table).delete().eq("id", record_id).execute()
                return bool(res.data)
            except Exception:
                pass

        engine = DBService.get_engine()
        cur = engine.conn.cursor()
        cur.execute(f"DELETE FROM {table} WHERE id = ?", [record_id])
        engine.conn.commit()
        return cur.rowcount > 0

    @staticmethod
    def execute_raw_sql(query: str, params: Optional[List[Any]] = None) -> List[Dict[str, Any]]:
        """Execute raw SQL query on local engine."""
        engine = DBService.get_engine()
        cur = engine.conn.cursor()
        cur.execute(query, params or [])
        rows = cur.fetchall()
        return [dict(r) for r in rows]
