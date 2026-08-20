-- ============================================================================
-- GIM CAMPUS MOBILITY AGGREGATOR - COMPLETE ONE-SHOT SUPABASE SETUP SCRIPT
-- Run this entire script in Supabase SQL Editor (Creates Tables + Seed Fleet)
-- ============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ----------------------------------------------------------------------------
-- STEP 1: CREATE TABLES
-- ----------------------------------------------------------------------------

-- 1. PROFILES
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    full_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    phone TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('student', 'driver', 'provider', 'admin')),
    program TEXT,
    password_hash TEXT NOT NULL DEFAULT '47c6ad3b9a495d6235470d1f9bd5111f98295eb0519e682dc28f5fdde7f5eec9', -- Default sha256 for gim@123
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_student_email CHECK (
        role != 'student' OR email LIKE '%@gim.ac.in'
    )
);

-- Ensure password_hash column exists if profiles was created earlier
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS password_hash TEXT DEFAULT '47c6ad3b9a495d6235470d1f9bd5111f98295eb0519e682dc28f5fdde7f5eec9';
UPDATE public.profiles SET password_hash = '47c6ad3b9a495d6235470d1f9bd5111f98295eb0519e682dc28f5fdde7f5eec9' WHERE password_hash IS NULL;

-- 2. DRIVERS / PROVIDERS
CREATE TABLE IF NOT EXISTS public.drivers (
    id UUID PRIMARY KEY REFERENCES public.profiles(id) ON DELETE CASCADE,
    business_name TEXT,
    provider_type TEXT NOT NULL CHECK (provider_type IN ('individual_driver', 'rental_agency')),
    license_number TEXT NOT NULL,
    id_proof_url TEXT,
    is_verified BOOLEAN NOT NULL DEFAULT false,
    is_available BOOLEAN NOT NULL DEFAULT true,
    rating NUMERIC(3, 2) NOT NULL DEFAULT 5.00 CHECK (rating >= 1.0 AND rating <= 5.0),
    total_completed_trips INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3. VEHICLES
CREATE TABLE IF NOT EXISTS public.vehicles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    provider_id UUID NOT NULL REFERENCES public.drivers(id) ON DELETE CASCADE,
    service_segment TEXT NOT NULL CHECK (service_segment IN ('Cab', 'Self-Drive')),
    vehicle_category TEXT NOT NULL CHECK (vehicle_category IN ('4-Wheeler', '2-Wheeler', 'Cab')),
    vehicle_type TEXT NOT NULL CHECK (vehicle_type IN ('Hatchback', 'Sedan', 'SUV', 'Scooty', 'Bike', 'Standard Cab')),
    vehicle_model TEXT NOT NULL,
    vehicle_number TEXT NOT NULL UNIQUE,
    seating_capacity INT NOT NULL DEFAULT 4,
    is_active BOOLEAN NOT NULL DEFAULT true,
    is_available BOOLEAN NOT NULL DEFAULT true,
    pricing_details JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 4. STANDARD ROUTES
CREATE TABLE IF NOT EXISTS public.standard_routes (
    id SERIAL PRIMARY KEY,
    origin TEXT NOT NULL DEFAULT 'GIM Campus (Sanquelim)',
    destination TEXT NOT NULL,
    estimated_fare_cab NUMERIC(10, 2) NOT NULL
);

-- 5. BOOKINGS
CREATE TABLE IF NOT EXISTS public.bookings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID NOT NULL REFERENCES public.profiles(id),
    vehicle_id UUID NOT NULL REFERENCES public.vehicles(id),
    provider_id UUID NOT NULL REFERENCES public.drivers(id),
    service_segment TEXT NOT NULL CHECK (service_segment IN ('Cab', 'Self-Drive')),
    vehicle_category TEXT NOT NULL,
    vehicle_type TEXT NOT NULL,
    pickup_location TEXT NOT NULL,
    dropoff_location TEXT NOT NULL,
    start_datetime TIMESTAMPTZ NOT NULL,
    end_datetime TIMESTAMPTZ,
    passengers_count INT NOT NULL DEFAULT 1,
    rental_duration_days_or_hours TEXT,
    base_trip_fare NUMERIC(10, 2) NOT NULL,
    convenience_fee NUMERIC(10, 2) NOT NULL DEFAULT 20.00,
    fee_payment_status TEXT NOT NULL DEFAULT 'pending' CHECK (fee_payment_status IN ('pending', 'paid')),
    booking_status TEXT NOT NULL DEFAULT 'requested' CHECK (booking_status IN ('requested', 'confirmed', 'in_progress', 'completed', 'cancelled')),
    priority_level TEXT NOT NULL DEFAULT 'standard' CHECK (priority_level IN ('standard', 'urgent', 'emergency')),
    special_notes TEXT DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 6. COMPLAINTS
CREATE TABLE IF NOT EXISTS public.complaints (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    booking_id UUID NOT NULL REFERENCES public.bookings(id) ON DELETE CASCADE,
    raised_by_id UUID NOT NULL REFERENCES public.profiles(id),
    target_user_id UUID REFERENCES public.profiles(id),
    complaint_type TEXT NOT NULL CHECK (complaint_type IN ('overcharging', 'cancellation', 'vehicle_condition', 'safety', 'driver_behavior', 'other')),
    description TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'under_investigation', 'resolved', 'dismissed')),
    priority TEXT NOT NULL DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    admin_notes TEXT DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 7. REVIEWS
CREATE TABLE IF NOT EXISTS public.reviews (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    booking_id UUID NOT NULL REFERENCES public.bookings(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES public.profiles(id),
    provider_id UUID NOT NULL REFERENCES public.drivers(id),
    rating INT NOT NULL CHECK (rating >= 1 AND rating <= 5),
    comment TEXT DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 8. ANALYTICS EVENTS
CREATE TABLE IF NOT EXISTS public.analytics_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    event_name TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ----------------------------------------------------------------------------
-- STEP 2: CREATE INDEXES
-- ----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_vehicles_search ON public.vehicles (service_segment, vehicle_category, vehicle_type, is_available, is_active);
CREATE INDEX IF NOT EXISTS idx_bookings_student ON public.bookings (student_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_bookings_provider ON public.bookings (provider_id, booking_status);
CREATE INDEX IF NOT EXISTS idx_bookings_vehicle_active ON public.bookings (vehicle_id, booking_status) WHERE booking_status IN ('requested', 'confirmed', 'in_progress');
CREATE INDEX IF NOT EXISTS idx_analytics_events_name_time ON public.analytics_events (event_name, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_complaints_status_priority ON public.complaints (status, priority);

-- ----------------------------------------------------------------------------
-- STEP 3: CONCURRENCY LOCK TRIGGER
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.check_vehicle_double_booking()
RETURNS TRIGGER AS $$
DECLARE
    conflict_count INT;
BEGIN
    IF NEW.booking_status IN ('confirmed', 'in_progress') THEN
        SELECT COUNT(*) INTO conflict_count
        FROM public.bookings
        WHERE vehicle_id = NEW.vehicle_id
          AND id != NEW.id
          AND booking_status IN ('confirmed', 'in_progress')
          AND (
            (NEW.end_datetime IS NULL AND start_datetime::date = NEW.start_datetime::date)
            OR
            (NEW.end_datetime IS NOT NULL AND (
                (NEW.start_datetime, NEW.end_datetime) OVERLAPS (start_datetime, COALESCE(end_datetime, start_datetime + INTERVAL '4 hours'))
            ))
          );

        IF conflict_count > 0 THEN
            RAISE EXCEPTION 'Concurrency Conflict: Vehicle is already booked for the specified time slot.';
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_prevent_double_booking ON public.bookings;
CREATE TRIGGER trg_prevent_double_booking
BEFORE INSERT OR UPDATE ON public.bookings
FOR EACH ROW
EXECUTE FUNCTION public.check_vehicle_double_booking();

-- ----------------------------------------------------------------------------
-- STEP 4: SEED DATA (PROFILES, DRIVERS, ROUTES, FLEET)
-- ----------------------------------------------------------------------------

-- Profiles
INSERT INTO public.profiles (id, full_name, email, phone, role, program, is_active, created_at) VALUES
('11111111-1111-1111-1111-111111111101', 'Aravind Krishnan', 'aravind.k24@gim.ac.in', '+91 98231 45678', 'student', 'PGDM Core', true, NOW() - INTERVAL '30 days'),
('11111111-1111-1111-1111-111111111102', 'Priya Sharma', 'priya.s24@gim.ac.in', '+91 98450 12345', 'student', 'BDA (Big Data Analytics)', true, NOW() - INTERVAL '28 days'),
('11111111-1111-1111-1111-111111111103', 'Rohit Mehta', 'rohit.m24@gim.ac.in', '+91 97654 89012', 'student', 'HCM (Healthcare Mgmt)', true, NOW() - INTERVAL '25 days'),
('11111111-1111-1111-1111-111111111104', 'Ananya Deshmukh', 'ananya.d24@gim.ac.in', '+91 94238 67890', 'student', 'BIFS (Banking & Finance)', true, NOW() - INTERVAL '20 days'),
('11111111-1111-1111-1111-111111111105', 'Varun Kapoor', 'varun.k24@gim.ac.in', '+91 98811 22334', 'student', 'PGDM Core', false, NOW() - INTERVAL '15 days'),
('22222222-2222-2222-2222-222222222201', 'Rajesh Naik', 'rajesh.cabs@pondataxi.com', '+91 98221 55667', 'driver', NULL, true, NOW() - INTERVAL '60 days'),
('22222222-2222-2222-2222-222222222202', 'Ganesh Gaonkar', 'ganesh.sanquelim@gmail.com', '+91 94220 66778', 'driver', NULL, true, NOW() - INTERVAL '50 days'),
('22222222-2222-2222-2222-222222222203', 'Sandeep Prabhu', 'sandeep@royalselfdrivegoa.in', '+91 98224 88990', 'provider', NULL, true, NOW() - INTERVAL '45 days'),
('22222222-2222-2222-2222-222222222204', 'Premanand Sawant', 'sawant.rentals@bicholim.com', '+91 97645 11223', 'provider', NULL, true, NOW() - INTERVAL '40 days'),
('22222222-2222-2222-2222-222222222205', 'Anthony D Souza', 'anthony.tours@goa.in', '+91 98901 33445', 'driver', NULL, false, NOW() - INTERVAL '10 days'),
('33333333-3333-3333-3333-333333333301', 'Campus Transport Admin', 'transport.admin@gim.ac.in', '+91 832 2366700', 'admin', 'Administration', true, NOW() - INTERVAL '90 days')
ON CONFLICT (id) DO NOTHING;

-- Drivers
INSERT INTO public.drivers (id, business_name, provider_type, license_number, id_proof_url, is_verified, is_available, rating, total_completed_trips, created_at) VALUES
('22222222-2222-2222-2222-222222222201', 'Sanquelim-GIM Taxi Union', 'individual_driver', 'GA-04-20160004521', 'https://gim-mobility.storage/docs/kyc_rajesh.pdf', true, true, 4.9, 142, NOW() - INTERVAL '60 days'),
('22222222-2222-2222-2222-222222222202', 'Ponda Premier Cabs', 'individual_driver', 'GA-05-20180009812', 'https://gim-mobility.storage/docs/kyc_ganesh.pdf', true, true, 4.7, 98, NOW() - INTERVAL '50 days'),
('22222222-2222-2222-2222-222222222203', 'Royal Self Drive Goa (Sanquelim Branch)', 'rental_agency', 'GA-04-20150001123', 'https://gim-mobility.storage/docs/kyc_royal.pdf', true, true, 4.8, 215, NOW() - INTERVAL '45 days'),
('22222222-2222-2222-2222-222222222204', 'Bicholim Two-Wheeler Hub', 'rental_agency', 'GA-04-20200007654', 'https://gim-mobility.storage/docs/kyc_bicholim.pdf', true, true, 4.6, 180, NOW() - INTERVAL '40 days'),
('22222222-2222-2222-2222-222222222205', 'Coastal Goa Fast Cabs', 'individual_driver', 'GA-01-20220003344', 'https://gim-mobility.storage/docs/kyc_anthony.pdf', false, false, 3.2, 12, NOW() - INTERVAL '10 days')
ON CONFLICT (id) DO NOTHING;

-- Standard Routes (14 destinations)
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
('GIM Campus, Sanquelim', 'Palolem / South Goa', 1780.00)
ON CONFLICT DO NOTHING;

-- Vehicles
INSERT INTO public.vehicles (id, provider_id, service_segment, vehicle_category, vehicle_type, vehicle_model, vehicle_number, seating_capacity, is_active, is_available, pricing_details, created_at) VALUES
-- Cabs
('44444444-4444-4444-4444-444444444401', '22222222-2222-2222-2222-222222222201', 'Cab', 'Cab', 'Sedan', 'Maruti Suzuki Dzire (AC Sedan)', 'GA-04-T-1289', 4, true, true, '{"tier": "Sedan", "base_fare": 80, "rate_per_km": 22}'::jsonb, NOW() - INTERVAL '50 days'),
('44444444-4444-4444-4444-444444444402', '22222222-2222-2222-2222-222222222201', 'Cab', 'Cab', 'SUV', 'Maruti Suzuki Ertiga (6+1 Seater SUV)', 'GA-04-T-8842', 7, true, true, '{"tier": "SUV", "base_fare": 100, "rate_per_km": 25}'::jsonb, NOW() - INTERVAL '40 days'),
('44444444-4444-4444-4444-444444444403', '22222222-2222-2222-2222-222222222202', 'Cab', 'Cab', 'SUV', 'Toyota Innova Crysta (Luxury 7-Seater)', 'GA-05-T-5511', 7, true, true, '{"tier": "SUV", "base_fare": 100, "rate_per_km": 25}'::jsonb, NOW() - INTERVAL '35 days'),
('44444444-4444-4444-4444-444444444404', '22222222-2222-2222-2222-222222222202', 'Cab', 'Cab', 'Hatchback', 'Maruti Suzuki WagonR (AC Hatchback)', 'GA-05-T-9921', 4, true, true, '{"tier": "Hatchback", "base_fare": 60, "rate_per_km": 20}'::jsonb, NOW() - INTERVAL '30 days'),

-- Self-Drive 4-Wheelers
('44444444-4444-4444-4444-444444444405', '22222222-2222-2222-2222-222222222203', 'Self-Drive', '4-Wheeler', 'Hatchback', 'Maruti Suzuki Swift (5 Seater)', 'GA-04-Z-2211', 5, true, true, '{"hourly_rate": 70, "daily_rate": 1680, "security_deposit": 2000, "fuel_type": "Petrol"}'::jsonb, NOW() - INTERVAL '45 days'),
('44444444-4444-4444-4444-444444444406', '22222222-2222-2222-2222-222222222203', 'Self-Drive', '4-Wheeler', 'Hatchback', 'Hyundai i20 Asta (5 Seater)', 'GA-04-Z-6677', 5, true, true, '{"hourly_rate": 70, "daily_rate": 1680, "security_deposit": 2500, "fuel_type": "Petrol"}'::jsonb, NOW() - INTERVAL '40 days'),
('44444444-4444-4444-4444-444444444407', '22222222-2222-2222-2222-222222222203', 'Self-Drive', '4-Wheeler', 'Sedan', 'Honda City 5th Gen (5 Seater)', 'GA-04-Z-9900', 5, true, true, '{"hourly_rate": 70, "daily_rate": 1680, "security_deposit": 3000, "fuel_type": "Petrol"}'::jsonb, NOW() - INTERVAL '35 days'),
('44444444-4444-4444-4444-444444444408', '22222222-2222-2222-2222-222222222203', 'Self-Drive', '4-Wheeler', 'SUV', 'Mahindra Thar 4x4 (4 Seater)', 'GA-04-Z-4444', 4, true, true, '{"hourly_rate": 105, "daily_rate": 2520, "security_deposit": 5000, "fuel_type": "Diesel"}'::jsonb, NOW() - INTERVAL '30 days'),
('44444444-4444-4444-4444-444444444409', '22222222-2222-2222-2222-222222222203', 'Self-Drive', '4-Wheeler', 'SUV', 'Hyundai Creta SX (5 Seater)', 'GA-04-Z-1010', 5, true, true, '{"hourly_rate": 105, "daily_rate": 2520, "security_deposit": 4000, "fuel_type": "Petrol"}'::jsonb, NOW() - INTERVAL '25 days'),
('44444444-4444-4444-4444-444444444415', '22222222-2222-2222-2222-222222222203', 'Self-Drive', '4-Wheeler', 'SUV', 'Toyota Innova Crysta (7 Seater SUV)', 'GA-04-Z-7700', 7, true, true, '{"hourly_rate": 105, "daily_rate": 2520, "security_deposit": 5000, "fuel_type": "Diesel"}'::jsonb, NOW() - INTERVAL '20 days'),
('44444444-4444-4444-4444-444444444416', '22222222-2222-2222-2222-222222222203', 'Self-Drive', '4-Wheeler', 'SUV', 'Maruti Suzuki Ertiga (7 Seater SUV)', 'GA-04-Z-8811', 7, true, true, '{"hourly_rate": 105, "daily_rate": 2520, "security_deposit": 4000, "fuel_type": "Petrol"}'::jsonb, NOW() - INTERVAL '20 days'),

-- Self-Drive 2-Wheelers
('44444444-4444-4444-4444-444444444410', '22222222-2222-2222-2222-222222222204', 'Self-Drive', '2-Wheeler', 'Scooty', 'Honda Activa 6G (2 Seater)', 'GA-04-M-3344', 2, true, true, '{"hourly_rate": 40, "daily_rate": 600, "security_deposit": 500, "helmets_included": 2}'::jsonb, NOW() - INTERVAL '40 days'),
('44444444-4444-4444-4444-444444444411', '22222222-2222-2222-2222-222222222204', 'Self-Drive', '2-Wheeler', 'Scooty', 'TVS Jupiter 125 (2 Seater)', 'GA-04-M-7788', 2, true, true, '{"hourly_rate": 40, "daily_rate": 600, "security_deposit": 500, "helmets_included": 2}'::jsonb, NOW() - INTERVAL '35 days'),
('44444444-4444-4444-4444-444444444412', '22222222-2222-2222-2222-222222222204', 'Self-Drive', '2-Wheeler', 'Bike', 'Royal Enfield Hunter 350 (2 Seater)', 'GA-04-M-9112', 2, true, true, '{"hourly_rate": 55, "daily_rate": 1000, "security_deposit": 1000, "helmets_included": 2}'::jsonb, NOW() - INTERVAL '30 days'),
('44444444-4444-4444-4444-444444444413', '22222222-2222-2222-2222-222222222204', 'Self-Drive', '2-Wheeler', 'Bike', 'Royal Enfield Classic 350 (2 Seater)', 'GA-04-M-1199', 2, true, true, '{"hourly_rate": 55, "daily_rate": 1000, "security_deposit": 1000, "helmets_included": 2}'::jsonb, NOW() - INTERVAL '25 days'),
('44444444-4444-4444-4444-444444444414', '22222222-2222-2222-2222-222222222204', 'Self-Drive', '2-Wheeler', 'Bike', 'Royal Enfield Himalayan 450 (2 Seater)', 'GA-04-M-5500', 2, true, true, '{"hourly_rate": 55, "daily_rate": 1100, "security_deposit": 1500, "helmets_included": 2}'::jsonb, NOW() - INTERVAL '20 days')
ON CONFLICT (id) DO NOTHING;

-- Bookings (Historical past completed trips)
INSERT INTO public.bookings (
    id, student_id, vehicle_id, provider_id, service_segment, vehicle_category, vehicle_type,
    pickup_location, dropoff_location, start_datetime, end_datetime, passengers_count,
    rental_duration_days_or_hours, base_trip_fare, convenience_fee, fee_payment_status,
    booking_status, priority_level, special_notes, created_at
) VALUES
('55555555-5555-5555-5555-555555555501', '11111111-1111-1111-1111-111111111101', '44444444-4444-4444-4444-444444444401', '22222222-2222-2222-2222-222222222201', 'Cab', 'Cab', 'Standard Cab',
'GIM Gate No. 2', 'Manohar Intl Airport (Mopa GOX)', NOW() - INTERVAL '5 days', NOW() - INTERVAL '5 days' + INTERVAL '1 hour 15 mins', 2,
'1.5 hours', 1800.00, 20.00, 'paid', 'completed', 'standard', 'Flight at 6:30 PM, on-time pickup required.', NOW() - INTERVAL '6 days'),

('55555555-5555-5555-5555-555555555502', '11111111-1111-1111-1111-111111111102', '44444444-4444-4444-4444-444444444405', '22222222-2222-2222-2222-222222222203', 'Self-Drive', '4-Wheeler', 'Hatchback',
'GIM Gate No. 2', 'North Goa Loop (Calangute, Anjuna)', NOW() - INTERVAL '3 days', NOW() - INTERVAL '2 days', 4,
'1 Day (24 hrs)', 1400.00, 20.00, 'paid', 'completed', 'standard', 'Weekend college trip.', NOW() - INTERVAL '4 days'),

('55555555-5555-5555-5555-555555555503', '11111111-1111-1111-1111-111111111103', '44444444-4444-4444-4444-444444444403', '22222222-2222-2222-2222-222222222202', 'Cab', 'Cab', 'Standard Cab',
'GIM Gate No. 2', 'Manipal Hospital Dona Paula', NOW() - INTERVAL '2 days', NOW() - INTERVAL '2 days' + INTERVAL '2 hours', 2,
'Outstation Hospital', 1600.00, 20.00, 'paid', 'completed', 'urgent', 'Medical appointment for student.', NOW() - INTERVAL '2 days' - INTERVAL '1 hour'),

('55555555-5555-5555-5555-555555555504', '11111111-1111-1111-1111-111111111104', '44444444-4444-4444-4444-444444444412', '22222222-2222-2222-2222-222222222204', 'Self-Drive', '2-Wheeler', 'Bike',
'GIM Gate No. 2', 'Panjim City Exploration', NOW() - INTERVAL '1 day', NOW() - INTERVAL '1 day' + INTERVAL '8 hours', 1,
'8 Hours', 750.00, 20.00, 'paid', 'completed', 'standard', 'Need helmet size L.', NOW() - INTERVAL '1 day' - INTERVAL '2 hours'),

('55555555-5555-5555-5555-555555555505', '11111111-1111-1111-1111-111111111101', '44444444-4444-4444-4444-444444444402', '22222222-2222-2222-2222-222222222201', 'Cab', 'Cab', 'Standard Cab',
'GIM Gate No. 2', 'Thivim Railway Station', NOW() - INTERVAL '6 hours', NOW() - INTERVAL '4 hours', 4,
'Direct Train Transfer', 700.00, 20.00, 'paid', 'completed', 'emergency', 'Vande Bharat Express transfer.', NOW() - INTERVAL '7 hours')
ON CONFLICT (id) DO NOTHING;

-- Reviews
INSERT INTO public.reviews (id, booking_id, student_id, provider_id, rating, comment, created_at) VALUES
('66666666-6666-6666-6666-666666666601', '55555555-5555-5555-5555-555555555501', '11111111-1111-1111-1111-111111111101', '22222222-2222-2222-2222-222222222201', 5, 'Super punctual! Rajesh bhaiya was waiting at Gate 2 early. Clean AC cab.', NOW() - INTERVAL '5 days'),
('66666666-6666-6666-6666-666666666602', '55555555-5555-5555-5555-555555555502', '11111111-1111-1111-1111-111111111102', '22222222-2222-2222-2222-222222222203', 5, 'Swift was in mint condition. Fast handover right at GIM Gate No. 2.', NOW() - INTERVAL '2 days')
ON CONFLICT (id) DO NOTHING;

-- Complaints
INSERT INTO public.complaints (id, booking_id, raised_by_id, target_user_id, complaint_type, description, status, priority, admin_notes, created_at) VALUES
('77777777-7777-7777-7777-777777777701', '55555555-5555-5555-5555-555555555501', '11111111-1111-1111-1111-111111111101', '22222222-2222-2222-2222-222222222201', 'driver_behavior', 'Driver took an alternate toll route without prior notice, though fare was respected.', 'resolved', 'low', 'Driver cautioned regarding route consultation prior to departure.', NOW() - INTERVAL '4 days')
ON CONFLICT (id) DO NOTHING;
