"""
Comprehensive Unit & Integration Test Suite for GIM Campus Mobility App.
Verifies domain validation, dynamic cascading queries, concurrency locking,
fee calculations, state transitions, complaints, and analytics.
"""
import sys
import os
import random
import datetime
import unittest

# Ensure workspace root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.config import (
    Role, ServiceSegment, VehicleCategory, VehicleType, BookingStatus,
    PriorityLevel, ComplaintStatus, ComplaintPriority, PLATFORM_CONVENIENCE_FEE,
    mask_phone_number
)
from src.db import DBService
from src.services.auth_service import AuthService
from src.services.vehicle_service import VehicleService
from src.services.booking_service import BookingService
from src.services.complaint_service import ComplaintService
from src.services.analytics_service import AnalyticsService


class TestGIMMobilityPlatform(unittest.TestCase):

    def test_01_domain_validation(self):
        """Verify strict @gim.ac.in domain enforcement for students."""
        valid, msg = AuthService.validate_student_email("aravind.k24@gim.ac.in")
        self.assertTrue(valid)

        valid2, msg2 = AuthService.validate_student_email("priya.sharma@gim.ac.in")
        self.assertTrue(valid2)

        # Invalid domains
        invalid, msg3 = AuthService.validate_student_email("student@gmail.com")
        self.assertFalse(invalid)
        self.assertIn("@gim.ac.in", msg3)

        invalid2, msg4 = AuthService.validate_student_email("hacker@othercollege.edu")
        self.assertFalse(invalid2)

    def test_02_phone_masking(self):
        """Verify phone masking privacy rule."""
        raw_phone = "+91 98221 55667"
        masked = mask_phone_number(raw_phone, is_unmasked=False)
        self.assertIn("***", masked)
        self.assertNotIn("55667", masked)

        unmasked = mask_phone_number(raw_phone, is_unmasked=True)
        self.assertEqual(unmasked, raw_phone)

    def test_03_dynamic_routes_and_vehicles(self):
        """Verify dynamic route and vehicle search."""
        routes = VehicleService.get_standard_routes()
        self.assertGreater(len(routes), 0)
        destinations = [r["destination"] for r in routes]
        self.assertTrue(any("Airport" in d for d in destinations))

        # Search Cabs across tiers
        cabs = VehicleService.search_available_vehicles(
            segment=ServiceSegment.CAB.value,
            category="Cab",
            only_verified=True
        )
        self.assertGreater(len(cabs), 0)
        self.assertEqual(cabs[0]["service_segment"], "Cab")

        # Search Self-Drive 4-Wheelers
        four_wheelers = VehicleService.search_available_vehicles(
            segment=ServiceSegment.SELF_DRIVE.value,
            category=VehicleCategory.FOUR_WHEELER.value,
            only_verified=True
        )
        self.assertGreater(len(four_wheelers), 0)

        # Search Self-Drive 2-Wheelers
        two_wheelers = VehicleService.search_available_vehicles(
            segment=ServiceSegment.SELF_DRIVE.value,
            category=VehicleCategory.TWO_WHEELER.value,
            only_verified=True
        )
        self.assertGreater(len(two_wheelers), 0)

    def test_04_booking_creation_and_fee_flow(self):
        """Verify booking creation with flat Rs.20 convenience fee and 0% provider commission."""
        students = AuthService.get_students()
        cabs = VehicleService.search_available_vehicles(segment=ServiceSegment.CAB.value)
        self.assertTrue(len(students) > 0 and len(cabs) > 0)

        student = students[0]
        cab = cabs[0]

        import random
        rand_days = random.randint(100, 500)
        start_dt = (datetime.datetime.now() + datetime.timedelta(days=rand_days, hours=10)).isoformat()
        end_dt = (datetime.datetime.now() + datetime.timedelta(days=rand_days, hours=12)).isoformat()

        ok, msg, booking = BookingService.create_booking_request(
            student_id=student["id"],
            vehicle_id=cab["id"],
            provider_id=cab["provider_id"],
            service_segment="Cab",
            vehicle_category="Cab",
            vehicle_type=cab.get("vehicle_type", "Sedan"),
            pickup_location="GIM Main Gate",
            dropoff_location="Mopa Airport (MOPA)",
            start_datetime=start_dt,
            end_datetime=end_dt,
            passengers_count=2,
            rental_duration="2 hours",
            base_trip_fare=1004.0,
            priority_level=PriorityLevel.STANDARD.value,
            special_notes="Test Booking",
            auto_pay_fee=True
        )
        self.assertTrue(ok)
        self.assertEqual(booking["convenience_fee"], PLATFORM_CONVENIENCE_FEE)
        self.assertEqual(booking["fee_payment_status"], "paid")
        self.assertEqual(booking["booking_status"], BookingStatus.CONFIRMED.value)

        # Test Concurrency Lock (Double booking prevention on overlapping slot)
        overlap_start = (datetime.datetime.now() + datetime.timedelta(days=rand_days, hours=10, minutes=30)).isoformat()
        overlap_end = (datetime.datetime.now() + datetime.timedelta(days=rand_days, hours=11, minutes=30)).isoformat()

        conflict_ok, conflict_msg, _ = BookingService.create_booking_request(
            student_id=student["id"],
            vehicle_id=cab["id"],
            provider_id=cab["provider_id"],
            service_segment="Cab",
            vehicle_category="Cab",
            vehicle_type=cab.get("vehicle_type", "Sedan"),
            pickup_location="GIM Admin",
            dropoff_location="Panjim (Panaji)",
            start_datetime=overlap_start,
            end_datetime=overlap_end,
            passengers_count=1,
            rental_duration="1 hour",
            base_trip_fare=762.0,
            auto_pay_fee=True
        )
        self.assertFalse(conflict_ok)
        self.assertIn("already scheduled/booked", conflict_msg)

        # Clean up test booking
        if booking and "id" in booking:
            DBService.delete("bookings", booking["id"])

    def test_05_complaints_and_resolution(self):
        """Verify grievance ticket filing and resolution update."""
        students = AuthService.get_students()
        bookings = BookingService.get_all_bookings()
        self.assertTrue(len(students) > 0 and len(bookings) > 0)

        ok, msg, comp = ComplaintService.file_complaint(
            booking_id=bookings[0]["id"],
            raised_by_id=students[0]["id"],
            target_user_id=bookings[0].get("provider_id"),
            complaint_type="overcharging",
            description="Driver asked for extra parking fare.",
            priority=ComplaintPriority.HIGH.value
        )
        self.assertTrue(ok)
        self.assertEqual(comp["status"], ComplaintStatus.OPEN.value)

        # Update ticket
        up_ok = ComplaintService.update_complaint_status(
            complaint_id=comp["id"],
            status=ComplaintStatus.RESOLVED.value,
            admin_notes="Refund processed and driver warned."
        )
        self.assertTrue(up_ok)

    def test_06_analytics_service(self):
        """Verify analytics funnel, route popularity, and financial summary."""
        funnel = AnalyticsService.get_funnel_metrics()
        self.assertEqual(len(funnel), 5)
        self.assertIn("Conversion Rate (%)", funnel.columns)

        routes_df = AnalyticsService.get_route_popularity()
        self.assertGreater(len(routes_df), 0)

        dist_df = AnalyticsService.get_vehicle_segment_distribution()
        self.assertEqual(len(dist_df), 3)

        fin = AnalyticsService.get_financial_summary()
        self.assertGreater(fin["platform_convenience_fees"], 0)
        self.assertGreater(fin["total_driver_earnings_retained"], 0)

    def test_07_distance_and_tiered_fare(self):
        """Verify OpenStreetMap distance resolution and tiered cab fares."""
        from src.services.distance_service import DistanceService, GOA_GEO_POINTS

        # Test Geo Points
        self.assertIn("GIM Campus, Sanquelim", GOA_GEO_POINTS)
        self.assertIn("Panjim (Panaji)", GOA_GEO_POINTS)
        self.assertIn("Mopa Airport (MOPA)", GOA_GEO_POINTS)
        self.assertIn("Goa Airport (Dabolim)", GOA_GEO_POINTS)

        # Distance calculation
        dist, dur, _ = DistanceService.get_route_distance("GIM Campus, Sanquelim", "Panjim (Panaji)")
        self.assertGreater(dist, 20.0)

        # Tiered Fare Verification
        # Hatchback: 60 + 20 * 40 = 860
        h_fare = DistanceService.calculate_fare(40.0, "Hatchback")
        self.assertEqual(h_fare["total_fare"], 860.0)
        self.assertEqual(h_fare["base_fare"], 60.0)
        self.assertEqual(h_fare["rate_per_km"], 20.0)

        # Sedan: 80 + 22 * 40 = 960
        s_fare = DistanceService.calculate_fare(40.0, "Sedan")
        self.assertEqual(s_fare["total_fare"], 960.0)
        self.assertEqual(s_fare["base_fare"], 80.0)
        self.assertEqual(s_fare["rate_per_km"], 22.0)

        # SUV: 100 + 25 * 40 = 1100
        suv_fare = DistanceService.calculate_fare(40.0, "SUV")
        self.assertEqual(suv_fare["total_fare"], 1100.0)
        self.assertEqual(suv_fare["base_fare"], 100.0)
        self.assertEqual(suv_fare["rate_per_km"], 25.0)

    def test_08_passenger_capacity_filtering(self):
        """Verify that cabs enforce (n-1) passenger seats for driver, and self-drive enforces n seats."""
        # 4-seater cab (e.g. Dzire / WagonR) has only 3 passenger seats
        cabs_3_pax = VehicleService.search_available_vehicles(segment=ServiceSegment.CAB.value, min_passengers=3)
        self.assertGreater(len(cabs_3_pax), 0)

        # For 4 passengers, only 6/7-seater SUVs (Ertiga, Innova Crysta) should match (4-seater cars only have 3 passenger seats)
        cabs_4_pax = VehicleService.search_available_vehicles(segment=ServiceSegment.CAB.value, min_passengers=4)
        for c in cabs_4_pax:
            total_seats = int(c.get("seating_capacity", 4))
            self.assertGreaterEqual(total_seats - 1, 4) # Must have at least 4 passenger seats + 1 driver

        # For Self-Drive: 2-wheelers seat max 2 persons
        sd_2_pax = VehicleService.search_available_vehicles(segment=ServiceSegment.SELF_DRIVE.value, category=VehicleCategory.TWO_WHEELER.value, min_passengers=2)
        self.assertGreater(len(sd_2_pax), 0)

        # 3 passengers cannot take a 2-wheeler
        sd_3_pax_bikes = VehicleService.search_available_vehicles(segment=ServiceSegment.SELF_DRIVE.value, category=VehicleCategory.TWO_WHEELER.value, min_passengers=3)
        self.assertEqual(len(sd_3_pax_bikes), 0)

    def test_09_self_drive_hourly_rates(self):
        """Verify flat self-drive hourly rates: SUV = 105/hr, Hatchback/Sedan = 70/hr, Bike = 55/hr, Scooty = 40/hr."""
        from src.config import SELF_DRIVE_HOURLY_RATES
        self.assertEqual(SELF_DRIVE_HOURLY_RATES["SUV"], 105.0)
        self.assertEqual(SELF_DRIVE_HOURLY_RATES["Hatchback"], 70.0)
        self.assertEqual(SELF_DRIVE_HOURLY_RATES["Sedan"], 70.0)
        self.assertEqual(SELF_DRIVE_HOURLY_RATES["Bike"], 55.0)
        self.assertEqual(SELF_DRIVE_HOURLY_RATES["Scooty"], 40.0)

        # 5 hours calculation
        dur_hrs = 5.0
        self.assertEqual(dur_hrs * SELF_DRIVE_HOURLY_RATES["SUV"], 525.0)
        self.assertEqual(dur_hrs * SELF_DRIVE_HOURLY_RATES["Hatchback"], 350.0)
        self.assertEqual(dur_hrs * SELF_DRIVE_HOURLY_RATES["Sedan"], 350.0)
        self.assertEqual(dur_hrs * SELF_DRIVE_HOURLY_RATES["Bike"], 275.0)
    def test_10_sha256_auth_and_registration(self):
        """Verify SHA-256 password encryption, multi-role login validation, and profile registration."""
        from src.config import hash_password, verify_password, DEFAULT_DEMO_PASSWORD

        # 1. SHA-256 Hashing and Verification
        plain_pw = "SuperSecret@2026"
        hashed_pw = hash_password(plain_pw)
        self.assertEqual(len(hashed_pw), 64) # SHA-256 produces 64-char hex digest
        self.assertTrue(verify_password(plain_pw, hashed_pw))
        self.assertFalse(verify_password("WrongPassword", hashed_pw))

        # 2. Existing Demo User Login
        auth_ok, msg, user = AuthService.authenticate_user("student", "aravind.k24@gim.ac.in", DEFAULT_DEMO_PASSWORD)
        self.assertTrue(auth_ok)
        self.assertEqual(user["role"], "student")

        # Wrong password fails
        bad_pw_ok, bad_msg, _ = AuthService.authenticate_user("student", "aravind.k24@gim.ac.in", "wrongPass123")
        self.assertFalse(bad_pw_ok)
        self.assertIn("Invalid password", bad_msg)

        # Wrong profile role selection fails
        wrong_role_ok, role_msg, _ = AuthService.authenticate_user("admin", "aravind.k24@gim.ac.in", DEFAULT_DEMO_PASSWORD)
        self.assertFalse(wrong_role_ok)
        self.assertIn("Access denied", role_msg)

        # 3. New Student Registration with SHA-256
        import uuid
        rand_suffix = str(uuid.uuid4())[:6]
        new_student_email = f"test.user_{rand_suffix}@gim.ac.in"
        reg_ok, reg_msg, new_student = AuthService.register_student(
            full_name="New Test Student",
            email=new_student_email,
            phone="+91 98999 11111",
            program="PGDM Core",
            password="MyStudentPass@123"
        )
        self.assertTrue(reg_ok)
        self.assertEqual(new_student["email"], new_student_email)
        self.assertEqual(new_student["password_hash"], hash_password("MyStudentPass@123"))

        # Log in with newly registered student
        login_new_ok, _, logged_in_std = AuthService.authenticate_user("student", new_student_email, "MyStudentPass@123")
        self.assertTrue(login_new_ok)
        self.assertEqual(logged_in_std["id"], new_student["id"])

        # 4. New Service Provider Registration with SHA-256
        new_pv_email = f"cabs_{rand_suffix}@goataxi.in"
        pv_reg_ok, pv_reg_msg, new_pv = AuthService.register_service_provider(
            full_name="Sanjay Naik",
            email=new_pv_email,
            phone="+91 97655 44332",
            business_name=f"Goa Fast Cabs {rand_suffix}",
            provider_type="individual_driver",
            license_number=f"GA-04-202400{rand_suffix}",
            password="ProviderPass@123"
        )
        self.assertTrue(pv_reg_ok)
        self.assertEqual(new_pv["role"], "driver")
        self.assertEqual(new_pv["password_hash"], hash_password("ProviderPass@123"))

        # Log in with newly registered provider
        login_pv_ok, _, logged_in_pv = AuthService.authenticate_user("provider", new_pv_email, "ProviderPass@123")
        self.assertTrue(login_pv_ok)
        self.assertEqual(logged_in_pv["id"], new_pv["id"])

        # Clean up test accounts
        if new_student and "id" in new_student:
            DBService.delete("profiles", new_student["id"])
        if new_pv and "id" in new_pv:
            DBService.delete("drivers", new_pv["id"])
            DBService.delete("profiles", new_pv["id"])


if __name__ == "__main__":
    unittest.main()
