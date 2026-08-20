-- ============================================================================
-- GIM CAMPUS MOBILITY AGGREGATOR - DATABASE SCHEMA (SUPABASE / POSTGRESQL DDL)
-- Target Platform: Goa Institute of Management (GIM), Sanquelim, Goa
-- ============================================================================

-- Enable UUID extension if not already active
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. PROFILES (Users)
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    full_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    phone TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('student', 'driver', 'provider', 'admin')),
    program TEXT, -- E.g. 'PGDM Core', 'BDA', 'HCM', 'BIFS', 'Faculty/Staff'
    password_hash TEXT NOT NULL DEFAULT '47c6ad3b9a495d6235470d1f9bd5111f98295eb0519e682dc28f5fdde7f5eec9', -- Default sha256 for gim@123
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_student_email CHECK (
        role != 'student' OR email LIKE '%@gim.ac.in'
    )
);

COMMENT ON TABLE public.profiles IS 'User profiles for students, drivers, rental providers, and campus admins';
COMMENT ON COLUMN public.profiles.email IS 'Strict @gim.ac.in constraint enforced for student accounts';

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

COMMENT ON TABLE public.drivers IS 'KYC, verification status, and metrics for drivers and rental agencies';

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
    pricing_details JSONB NOT NULL DEFAULT '{}'::jsonb, -- Rates per day/hour/km or fixed route pricing
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE public.vehicles IS 'Fleet inventory for cabs and self-drive cars/bikes';

-- 4. STANDARD ROUTES (For Cab Services originating/terminating at GIM)
CREATE TABLE IF NOT EXISTS public.standard_routes (
    id SERIAL PRIMARY KEY,
    origin TEXT NOT NULL DEFAULT 'GIM Campus (Sanquelim)',
    destination TEXT NOT NULL,
    estimated_fare_cab NUMERIC(10, 2) NOT NULL
);

COMMENT ON TABLE public.standard_routes IS 'Pre-negotiated transparent cab route fares from/to GIM campus';

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

COMMENT ON TABLE public.bookings IS 'Central booking records with 0% provider commission and flat Rs.20 convenience fee';

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

COMMENT ON TABLE public.complaints IS 'Dispute and grievance resolution system for campus admin';

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

COMMENT ON TABLE public.reviews IS 'Post-trip ratings and feedback';

-- 8. ANALYTICS EVENTS
CREATE TABLE IF NOT EXISTS public.analytics_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    event_name TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE public.analytics_events IS 'Clickstream and event logger for funnel drop-off and route demand analytics';

-- ============================================================================
-- INDEXES FOR SUB-SECOND SEARCH & CONCURRENCY
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_vehicles_search ON public.vehicles (service_segment, vehicle_category, vehicle_type, is_available, is_active);
CREATE INDEX IF NOT EXISTS idx_bookings_student ON public.bookings (student_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_bookings_provider ON public.bookings (provider_id, booking_status);
CREATE INDEX IF NOT EXISTS idx_bookings_vehicle_active ON public.bookings (vehicle_id, booking_status) WHERE booking_status IN ('requested', 'confirmed', 'in_progress');
CREATE INDEX IF NOT EXISTS idx_analytics_events_name_time ON public.analytics_events (event_name, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_complaints_status_priority ON public.complaints (status, priority);

-- ============================================================================
-- PREVENT DOUBLE BOOKING TRIGGER FUNCTION (OPTIMISTIC / CONCURRENCY LOCK)
-- ============================================================================
CREATE OR REPLACE FUNCTION public.check_vehicle_double_booking()
RETURNS TRIGGER AS $$
DECLARE
    conflict_count INT;
BEGIN
    -- Check if vehicle is already booked in requested, confirmed, or in_progress status
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
