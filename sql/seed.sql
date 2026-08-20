-- ============================================================================
-- GIM CAMPUS MOBILITY AGGREGATOR - SEED DATA SCRIPT
-- Realistic Goa & GIM Community Datasets
-- ============================================================================

-- Clean existing data in reverse dependency order
TRUNCATE TABLE public.analytics_events CASCADE;
TRUNCATE TABLE public.reviews CASCADE;
TRUNCATE TABLE public.complaints CASCADE;
TRUNCATE TABLE public.bookings CASCADE;
TRUNCATE TABLE public.standard_routes CASCADE;
TRUNCATE TABLE public.vehicles CASCADE;
TRUNCATE TABLE public.drivers CASCADE;
TRUNCATE TABLE public.profiles CASCADE;

-- 1. SEED PROFILES
-- Students (Must have @gim.ac.in)
INSERT INTO public.profiles (id, full_name, email, phone, role, program, is_active, created_at) VALUES
('11111111-1111-1111-1111-111111111101', 'Aravind Krishnan', 'aravind.k24@gim.ac.in', '+91 98231 45678', 'student', 'PGDM Core', true, NOW() - INTERVAL '30 days'),
('11111111-1111-1111-1111-111111111102', 'Priya Sharma', 'priya.s24@gim.ac.in', '+91 98450 12345', 'student', 'BDA (Big Data Analytics)', true, NOW() - INTERVAL '28 days'),
('11111111-1111-1111-1111-111111111103', 'Rohit Mehta', 'rohit.m24@gim.ac.in', '+91 97654 89012', 'student', 'HCM (Healthcare Mgmt)', true, NOW() - INTERVAL '25 days'),
('11111111-1111-1111-1111-111111111104', 'Ananya Deshmukh', 'ananya.d24@gim.ac.in', '+91 94238 67890', 'student', 'BIFS (Banking & Finance)', true, NOW() - INTERVAL '20 days'),
('11111111-1111-1111-1111-111111111105', 'Varun Kapoor', 'varun.k24@gim.ac.in', '+91 98811 22334', 'student', 'PGDM Core', false, NOW() - INTERVAL '15 days');

-- Drivers & Providers
INSERT INTO public.profiles (id, full_name, email, phone, role, program, is_active, created_at) VALUES
('22222222-2222-2222-2222-222222222201', 'Rajesh Naik', 'rajesh.cabs@pondataxi.com', '+91 98221 55667', 'driver', NULL, true, NOW() - INTERVAL '60 days'),
('22222222-2222-2222-2222-222222222202', 'Ganesh Gaonkar', 'ganesh.sanquelim@gmail.com', '+91 94220 66778', 'driver', NULL, true, NOW() - INTERVAL '50 days'),
('22222222-2222-2222-2222-222222222203', 'Sandeep Prabhu', 'sandeep@royalselfdrivegoa.in', '+91 98224 88990', 'provider', NULL, true, NOW() - INTERVAL '45 days'),
('22222222-2222-2222-2222-222222222204', 'Premanand Sawant', 'sawant.rentals@bicholim.com', '+91 97645 11223', 'provider', NULL, true, NOW() - INTERVAL '40 days'),
('22222222-2222-2222-2222-222222222205', 'Anthony D Souza', 'anthony.tours@goa.in', '+91 98901 33445', 'driver', NULL, false, NOW() - INTERVAL '10 days');

-- Campus Admin
INSERT INTO public.profiles (id, full_name, email, phone, role, program, is_active, created_at) VALUES
('33333333-3333-3333-3333-333333333301', 'Campus Transport Admin', 'transport.admin@gim.ac.in', '+91 832 2366700', 'admin', 'Administration', true, NOW() - INTERVAL '90 days');

-- 2. SEED DRIVERS & PROVIDERS METADATA
INSERT INTO public.drivers (id, business_name, provider_type, license_number, id_proof_url, is_verified, is_available, rating, total_completed_trips, created_at) VALUES
('22222222-2222-2222-2222-222222222201', 'Sanquelim-GIM Taxi Union', 'individual_driver', 'GA-04-20160004521', 'https://gim-mobility.storage/docs/kyc_rajesh.pdf', true, true, 4.9, 142, NOW() - INTERVAL '60 days'),
('22222222-2222-2222-2222-222222222202', 'Ponda Premier Cabs', 'individual_driver', 'GA-05-20180009812', 'https://gim-mobility.storage/docs/kyc_ganesh.pdf', true, true, 4.7, 98, NOW() - INTERVAL '50 days'),
('22222222-2222-2222-2222-222222222203', 'Royal Self Drive Goa (Sanquelim Branch)', 'rental_agency', 'GA-04-20150001123', 'https://gim-mobility.storage/docs/kyc_royal.pdf', true, true, 4.8, 215, NOW() - INTERVAL '45 days'),
('22222222-2222-2222-2222-222222222204', 'Bicholim Two-Wheeler Hub', 'rental_agency', 'GA-04-20200007654', 'https://gim-mobility.storage/docs/kyc_bicholim.pdf', true, true, 4.6, 180, NOW() - INTERVAL '40 days'),
('22222222-2222-2222-2222-222222222205', 'Coastal Goa Fast Cabs', 'individual_driver', 'GA-01-20220003344', 'https://gim-mobility.storage/docs/kyc_anthony.pdf', false, false, 3.2, 12, NOW() - INTERVAL '10 days');

-- 3. SEED STANDARD CAB ROUTES (Originating or returning to GIM Sanquelim)
INSERT INTO public.standard_routes (origin, destination, estimated_fare_cab) VALUES
('GIM Campus, Sanquelim', 'Sanquelim Town', 110.00),
('GIM Campus, Sanquelim', 'Bicholim', 240.00),
('GIM Campus, Sanquelim', 'Mapusa', 580.00),
('GIM Campus, Sanquelim', 'Panjim (Panaji)', 680.00),
('GIM Campus, Sanquelim', 'Old Goa', 500.00),
('GIM Campus, Sanquelim', 'Calangute / Baga', 800.00),
('GIM Campus, Sanquelim', 'Anjuna / Vagator', 820.00),
('GIM Campus, Sanquelim', 'Candolim', 840.00),
('GIM Campus, Sanquelim', 'Goa Airport (Dabolim)', 1080.00),
('GIM Campus, Sanquelim', 'Mopa Airport (MOPA)', 900.00),
('GIM Campus, Sanquelim', 'Thivim Railway Station', 510.00),
('GIM Campus, Sanquelim', 'Karmali Railway Station', 560.00),
('GIM Campus, Sanquelim', 'Madgaon (Margao)', 1140.00),
('GIM Campus, Sanquelim', 'Palolem / South Goa', 1780.00);

-- 4. SEED VEHICLES
INSERT INTO public.vehicles (id, provider_id, service_segment, vehicle_category, vehicle_type, vehicle_model, vehicle_number, seating_capacity, is_active, is_available, pricing_details, created_at) VALUES
-- Cabs (Available Passenger Seats = seating_capacity - 1)
('44444444-4444-4444-4444-444444444401', '22222222-2222-2222-2222-222222222201', 'Cab', 'Cab', 'Sedan', 'Maruti Suzuki Dzire (AC Sedan)', 'GA-04-T-1289', 4, true, true, '{"tier": "Sedan", "base_fare": 80, "rate_per_km": 22}'::jsonb, NOW() - INTERVAL '50 days'),
('44444444-4444-4444-4444-444444444402', '22222222-2222-2222-2222-222222222201', 'Cab', 'Cab', 'SUV', 'Maruti Suzuki Ertiga (6+1 Seater SUV)', 'GA-04-T-8842', 7, true, true, '{"tier": "SUV", "base_fare": 100, "rate_per_km": 25}'::jsonb, NOW() - INTERVAL '40 days'),
('44444444-4444-4444-4444-444444444403', '22222222-2222-2222-2222-222222222202', 'Cab', 'Cab', 'SUV', 'Toyota Innova Crysta (Luxury 7-Seater)', 'GA-05-T-5511', 7, true, true, '{"tier": "SUV", "base_fare": 100, "rate_per_km": 25}'::jsonb, NOW() - INTERVAL '35 days'),
('44444444-4444-4444-4444-444444444404', '22222222-2222-2222-2222-222222222202', 'Cab', 'Cab', 'Hatchback', 'Maruti Suzuki WagonR (AC Hatchback)', 'GA-05-T-9921', 4, true, true, '{"tier": "Hatchback", "base_fare": 60, "rate_per_km": 20}'::jsonb, NOW() - INTERVAL '30 days'),

-- Self-Drive 4-Wheelers (Hourly Rate: ₹70/hr for Hatchback/Sedan, ₹105/hr for SUV)
('44444444-4444-4444-4444-444444444405', '22222222-2222-2222-2222-222222222203', 'Self-Drive', '4-Wheeler', 'Hatchback', 'Maruti Suzuki Swift (5 Seater)', 'GA-04-Z-2211', 5, true, true, '{"hourly_rate": 70, "daily_rate": 1680, "security_deposit": 2000, "fuel_type": "Petrol"}'::jsonb, NOW() - INTERVAL '45 days'),
('44444444-4444-4444-4444-444444444406', '22222222-2222-2222-2222-222222222203', 'Self-Drive', '4-Wheeler', 'Hatchback', 'Hyundai i20 Asta (5 Seater)', 'GA-04-Z-6677', 5, true, true, '{"hourly_rate": 70, "daily_rate": 1680, "security_deposit": 2500, "fuel_type": "Petrol"}'::jsonb, NOW() - INTERVAL '40 days'),
('44444444-4444-4444-4444-444444444407', '22222222-2222-2222-2222-222222222203', 'Self-Drive', '4-Wheeler', 'Sedan', 'Honda City 5th Gen (5 Seater)', 'GA-04-Z-9900', 5, true, true, '{"hourly_rate": 70, "daily_rate": 1680, "security_deposit": 3000, "fuel_type": "Petrol"}'::jsonb, NOW() - INTERVAL '35 days'),
('44444444-4444-4444-4444-444444444408', '22222222-2222-2222-2222-222222222203', 'Self-Drive', '4-Wheeler', 'SUV', 'Mahindra Thar 4x4 (4 Seater)', 'GA-04-Z-4444', 4, true, true, '{"hourly_rate": 105, "daily_rate": 2520, "security_deposit": 5000, "fuel_type": "Diesel"}'::jsonb, NOW() - INTERVAL '30 days'),
('44444444-4444-4444-4444-444444444409', '22222222-2222-2222-2222-222222222203', 'Self-Drive', '4-Wheeler', 'SUV', 'Hyundai Creta SX (5 Seater)', 'GA-04-Z-1010', 5, true, true, '{"hourly_rate": 105, "daily_rate": 2520, "security_deposit": 4000, "fuel_type": "Petrol"}'::jsonb, NOW() - INTERVAL '25 days'),
('44444444-4444-4444-4444-444444444415', '22222222-2222-2222-2222-222222222203', 'Self-Drive', '4-Wheeler', 'SUV', 'Toyota Innova Crysta (7 Seater SUV)', 'GA-04-Z-7700', 7, true, true, '{"hourly_rate": 105, "daily_rate": 2520, "security_deposit": 5000, "fuel_type": "Diesel"}'::jsonb, NOW() - INTERVAL '20 days'),
('44444444-4444-4444-4444-444444444416', '22222222-2222-2222-2222-222222222203', 'Self-Drive', '4-Wheeler', 'SUV', 'Maruti Suzuki Ertiga (7 Seater SUV)', 'GA-04-Z-8811', 7, true, true, '{"hourly_rate": 105, "daily_rate": 2520, "security_deposit": 4000, "fuel_type": "Petrol"}'::jsonb, NOW() - INTERVAL '20 days'),

-- Self-Drive 2-Wheelers (Seats = 2, Scooty: ₹40/hr, Bike: ₹55/hr)
('44444444-4444-4444-4444-444444444410', '22222222-2222-2222-2222-222222222204', 'Self-Drive', '2-Wheeler', 'Scooty', 'Honda Activa 6G (2 Seater)', 'GA-04-M-3344', 2, true, true, '{"hourly_rate": 40, "daily_rate": 600, "security_deposit": 500, "helmets_included": 2}'::jsonb, NOW() - INTERVAL '40 days'),
('44444444-4444-4444-4444-444444444411', '22222222-2222-2222-2222-222222222204', 'Self-Drive', '2-Wheeler', 'Scooty', 'TVS Jupiter 125 (2 Seater)', 'GA-04-M-7788', 2, true, true, '{"hourly_rate": 40, "daily_rate": 600, "security_deposit": 500, "helmets_included": 2}'::jsonb, NOW() - INTERVAL '35 days'),
('44444444-4444-4444-4444-444444444412', '22222222-2222-2222-2222-222222222204', 'Self-Drive', '2-Wheeler', 'Bike', 'Royal Enfield Hunter 350 (2 Seater)', 'GA-04-M-9112', 2, true, true, '{"hourly_rate": 55, "daily_rate": 1000, "security_deposit": 1000, "helmets_included": 2}'::jsonb, NOW() - INTERVAL '30 days'),
('44444444-4444-4444-4444-444444444413', '22222222-2222-2222-2222-222222222204', 'Self-Drive', '2-Wheeler', 'Bike', 'Royal Enfield Classic 350 (2 Seater)', 'GA-04-M-1199', 2, true, true, '{"hourly_rate": 55, "daily_rate": 1000, "security_deposit": 1000, "helmets_included": 2}'::jsonb, NOW() - INTERVAL '25 days'),
('44444444-4444-4444-4444-444444444414', '22222222-2222-2222-2222-222222222204', 'Self-Drive', '2-Wheeler', 'Bike', 'Royal Enfield Himalayan 450 (2 Seater)', 'GA-04-M-5500', 2, true, true, '{"hourly_rate": 55, "daily_rate": 1100, "security_deposit": 1500, "helmets_included": 2}'::jsonb, NOW() - INTERVAL '20 days');

-- 5. SEED BOOKINGS (All historical demo bookings stored as past completed trips so fleet is 100% free)
INSERT INTO public.bookings (
    id, student_id, vehicle_id, provider_id, service_segment, vehicle_category, vehicle_type,
    pickup_location, dropoff_location, start_datetime, end_datetime, passengers_count,
    rental_duration_days_or_hours, base_trip_fare, convenience_fee, fee_payment_status,
    booking_status, priority_level, special_notes, created_at
) VALUES
-- Completed Cab Trip
('55555555-5555-5555-5555-555555555501', '11111111-1111-1111-1111-111111111101', '44444444-4444-4444-4444-444444444401', '22222222-2222-2222-2222-222222222201', 'Cab', 'Cab', 'Standard Cab',
'GIM Gate No. 2', 'Manohar Intl Airport (Mopa GOX)', NOW() - INTERVAL '5 days', NOW() - INTERVAL '5 days' + INTERVAL '1 hour 15 mins', 2,
'1.5 hours', 1800.00, 20.00, 'paid', 'completed', 'standard', 'Flight at 6:30 PM, on-time pickup required.', NOW() - INTERVAL '6 days'),

-- Completed Self-Drive Trip
('55555555-5555-5555-5555-555555555502', '11111111-1111-1111-1111-111111111102', '44444444-4444-4444-4444-444444444405', '22222222-2222-2222-2222-222222222203', 'Self-Drive', '4-Wheeler', 'Hatchback',
'GIM Gate No. 2', 'North Goa Loop (Calangute, Anjuna)', NOW() - INTERVAL '3 days', NOW() - INTERVAL '2 days', 4,
'1 Day (24 hrs)', 1400.00, 20.00, 'paid', 'completed', 'standard', 'Weekend college trip.', NOW() - INTERVAL '4 days'),

-- Completed Hospital Cab Trip
('55555555-5555-5555-5555-555555555503', '11111111-1111-1111-1111-111111111103', '44444444-4444-4444-4444-444444444403', '22222222-2222-2222-2222-222222222202', 'Cab', 'Cab', 'Standard Cab',
'GIM Gate No. 2', 'Manipal Hospital Dona Paula', NOW() - INTERVAL '2 days', NOW() - INTERVAL '2 days' + INTERVAL '2 hours', 2,
'Outstation Hospital', 1600.00, 20.00, 'paid', 'completed', 'urgent', 'Medical appointment for student.', NOW() - INTERVAL '2 days' - INTERVAL '1 hour'),

-- Completed Self-Drive (2-Wheeler)
('55555555-5555-5555-5555-555555555504', '11111111-1111-1111-1111-111111111104', '44444444-4444-4444-4444-444444444412', '22222222-2222-2222-2222-222222222204', 'Self-Drive', '2-Wheeler', 'Bike',
'GIM Gate No. 2', 'Panjim City Exploration', NOW() - INTERVAL '1 day', NOW() - INTERVAL '1 day' + INTERVAL '8 hours', 1,
'8 Hours', 750.00, 20.00, 'paid', 'completed', 'standard', 'Need helmet size L.', NOW() - INTERVAL '1 day' - INTERVAL '2 hours'),

-- Completed Cab Booking
('55555555-5555-5555-5555-555555555505', '11111111-1111-1111-1111-111111111101', '44444444-4444-4444-4444-444444444402', '22222222-2222-2222-2222-222222222201', 'Cab', 'Cab', 'Standard Cab',
'GIM Gate No. 2', 'Thivim Railway Station', NOW() - INTERVAL '6 hours', NOW() - INTERVAL '4 hours', 4,
'Direct Train Transfer', 700.00, 20.00, 'paid', 'completed', 'emergency', 'Vande Bharat Express transfer.', NOW() - INTERVAL '7 hours');

-- 6. SEED REVIEWS
INSERT INTO public.reviews (id, booking_id, student_id, provider_id, rating, comment, created_at) VALUES
('66666666-6666-6666-6666-666666666601', '55555555-5555-5555-5555-555555555501', '11111111-1111-1111-1111-111111111101', '22222222-2222-2222-2222-222222222201', 5, 'Super punctual! Rajesh bhaiya was waiting at the hostel gate 10 mins early. Clean AC cab.', NOW() - INTERVAL '5 days'),
('66666666-6666-6666-6666-666666666602', '55555555-5555-5555-5555-555555555502', '11111111-1111-1111-1111-111111111102', '22222222-2222-2222-2222-222222222203', 5, 'Swift was in mint condition. Fast documentation and hassle-free return right at GIM main gate.', NOW() - INTERVAL '2 days');

-- 7. SEED COMPLAINTS
INSERT INTO public.complaints (id, booking_id, raised_by_id, target_user_id, complaint_type, description, status, priority, admin_notes, created_at) VALUES
('77777777-7777-7777-7777-777777777701', '55555555-5555-5555-5555-555555555501', '11111111-1111-1111-1111-111111111101', '22222222-2222-2222-2222-222222222201', 'driver_behavior', 'Driver took an alternate toll route without prior notice, though fare was respected.', 'resolved', 'low', 'Driver cautioned regarding route consultation prior to departure.', NOW() - INTERVAL '4 days'),
('77777777-7777-7777-7777-777777777702', '55555555-5555-5555-5555-555555555503', '11111111-1111-1111-1111-111111111103', '22222222-2222-2222-2222-222222222202', 'safety', 'Emergency medical ride dispatched - tracking vehicle live to ensure smooth corridor.', 'under_investigation', 'critical', 'Campus Health Center and Security in direct touch with driver Ganesh.', NOW() - INTERVAL '30 mins');

-- 8. SEED ANALYTICS EVENTS (Funnel & Clickstream Events)
INSERT INTO public.analytics_events (id, user_id, event_name, metadata, timestamp) VALUES
('88888888-8888-8888-8888-888888888801', '11111111-1111-1111-1111-111111111101', 'page_view', '{"page": "student_portal", "device": "mobile", "network": "GIM-WiFi"}'::jsonb, NOW() - INTERVAL '6 days'),
('88888888-8888-8888-8888-888888888802', '11111111-1111-1111-1111-111111111101', 'search_click', '{"segment": "Cab", "destination": "Manohar Intl Airport (Mopa GOX)"}'::jsonb, NOW() - INTERVAL '6 days'),
('88888888-8888-8888-8888-888888888803', '11111111-1111-1111-1111-111111111101', 'segment_selected', '{"segment": "Cab", "fare": 1800}'::jsonb, NOW() - INTERVAL '6 days'),
('88888888-8888-8888-8888-888888888804', '11111111-1111-1111-1111-111111111101', 'booking_started', '{"vehicle_type": "Standard Cab", "fee": 20}'::jsonb, NOW() - INTERVAL '6 days'),
('88888888-8888-8888-8888-888888888805', '11111111-1111-1111-1111-111111111101', 'booking_completed', '{"booking_id": "55555555-5555-5555-5555-555555555501", "payment": "UPI_SUCCESS"}'::jsonb, NOW() - INTERVAL '6 days'),

-- Additional Funnel Drop-off Simulation
('88888888-8888-8888-8888-888888888806', '11111111-1111-1111-1111-111111111102', 'page_view', '{"page": "student_portal"}'::jsonb, NOW() - INTERVAL '4 days'),
('88888888-8888-8888-8888-888888888807', '11111111-1111-1111-1111-111111111102', 'search_click', '{"segment": "Self-Drive", "category": "4-Wheeler"}'::jsonb, NOW() - INTERVAL '4 days'),
('88888888-8888-8888-8888-888888888808', '11111111-1111-1111-1111-111111111102', 'booking_started', '{"vehicle_type": "Hatchback", "fee": 20}'::jsonb, NOW() - INTERVAL '4 days'),
('88888888-8888-8888-8888-888888888809', '11111111-1111-1111-1111-111111111102', 'booking_completed', '{"booking_id": "55555555-5555-5555-5555-555555555502"}'::jsonb, NOW() - INTERVAL '4 days'),

-- Abandoned Session Simulation
('88888888-8888-8888-8888-888888888810', '11111111-1111-1111-1111-111111111105', 'page_view', '{"page": "student_portal"}'::jsonb, NOW() - INTERVAL '2 days'),
('88888888-8888-8888-8888-888888888811', '11111111-1111-1111-1111-111111111105', 'search_click', '{"segment": "Self-Drive", "category": "2-Wheeler"}'::jsonb, NOW() - INTERVAL '2 days'),
('88888888-8888-8888-8888-888888888812', '11111111-1111-1111-1111-111111111105', 'booking_abandoned', '{"reason": "payment_timeout", "step": "upi_fee"}'::jsonb, NOW() - INTERVAL '2 days');
