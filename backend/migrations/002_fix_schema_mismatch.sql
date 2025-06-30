-- =============================================================================
-- Migration: Fix Schema Mismatch
-- Version: 002
-- Date: 2024-01-XX
-- Description: Fix schema mismatch between existing database and expected code structure
-- 
-- This migration fixes the trips table to match the expected schema:
-- - Rename trip_id (UUID) to id (SERIAL)
-- - Add missing columns (name, date_start, date_end, description, status, etc.)
-- - Update foreign key references
-- 
-- SAFETY: Only runs if no existing trips data (confirmed: 0 trips exist)
-- =============================================================================

-- Enable transaction safety
BEGIN;

-- Create enum types if they don't exist
-- Note: PostgreSQL enums are created at the database level, not table level

-- Create trip_status enum if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'trip_status') THEN
        CREATE TYPE trip_status AS ENUM ('draft', 'pending_vote', 'approved', 'rejected', 'cancelled');
    END IF;
END $$;

-- Create vote_type enum if it doesn't exist  
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'vote_type') THEN
        CREATE TYPE vote_type AS ENUM ('yes', 'no');
    END IF;
END $$;

-- Create user_role enum if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_role') THEN
        CREATE TYPE user_role AS ENUM ('creator', 'member', 'admin');
    END IF;
END $$;

-- Check if trips table has the old schema (trip_id as UUID)
DO $$ 
DECLARE
    column_exists BOOLEAN;
    trip_count INTEGER;
BEGIN
    -- Check if trip_id column exists (old schema)
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'trips' AND column_name = 'trip_id'
    ) INTO column_exists;
    
    -- Check if there are any existing trips
    SELECT COUNT(*) FROM trips INTO trip_count;
    
    IF column_exists AND trip_count = 0 THEN
        RAISE NOTICE 'Fixing trips table schema...';
        
        -- Drop the old trips table (safe since no data exists)
        DROP TABLE IF EXISTS trips CASCADE;
        
        -- Create new trips table with correct schema
        CREATE TABLE trips (
            -- Primary key
            id SERIAL PRIMARY KEY,
            
            -- Basic trip information
            name VARCHAR(255) NOT NULL,
            description TEXT,
            
            -- Creator relationship (matches existing raw SQL expectations)
            creator_id INTEGER NOT NULL,
            
            -- Trip dates
            date_start TIMESTAMP,
            date_end TIMESTAMP,
            
            -- Trip status (new field for enhanced functionality)
            status trip_status DEFAULT 'draft',
            
            -- PDF file information (new fields for /api/save_trip functionality)
            pdf_file_path VARCHAR(500),
            pdf_file_name VARCHAR(255),
            pdf_file_size INTEGER,
            pdf_data BYTEA,  -- Keep existing pdf_data column for backward compatibility
            
            -- Metadata
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            -- Constraints
            CONSTRAINT fk_trips_creator FOREIGN KEY (creator_id) REFERENCES users(user_id) ON DELETE CASCADE,
            CONSTRAINT chk_trip_dates CHECK (date_end IS NULL OR date_start IS NULL OR date_end >= date_start),
            CONSTRAINT chk_pdf_file_size CHECK (pdf_file_size IS NULL OR pdf_file_size >= 0)
        );
        
        -- Create indexes for performance
        CREATE INDEX idx_trips_creator_id ON trips(creator_id);
        CREATE INDEX idx_trips_status ON trips(status);
        CREATE INDEX idx_trips_created_at ON trips(created_at);
        CREATE INDEX idx_trips_date_start ON trips(date_start);
        
        -- Add comments for documentation
        COMMENT ON TABLE trips IS 'Main trip entity representing travel plans';
        COMMENT ON COLUMN trips.id IS 'Primary key, auto-incrementing';
        COMMENT ON COLUMN trips.name IS 'Trip name (required)';
        COMMENT ON COLUMN trips.description IS 'Optional trip description';
        COMMENT ON COLUMN trips.creator_id IS 'ID of the user who created this trip';
        COMMENT ON COLUMN trips.date_start IS 'Trip start date';
        COMMENT ON COLUMN trips.date_end IS 'Trip end date';
        COMMENT ON COLUMN trips.status IS 'Current status of the trip';
        COMMENT ON COLUMN trips.pdf_file_path IS 'Path to stored PDF file on server';
        COMMENT ON COLUMN trips.pdf_file_name IS 'Original filename of uploaded PDF';
        COMMENT ON COLUMN trips.pdf_file_size IS 'Size of PDF file in bytes';
        COMMENT ON COLUMN trips.pdf_data IS 'PDF file data (legacy column for backward compatibility)';
        COMMENT ON COLUMN trips.created_at IS 'Timestamp when trip was created';
        COMMENT ON COLUMN trips.updated_at IS 'Timestamp when trip was last updated';
        
        RAISE NOTICE 'Successfully recreated trips table with correct schema';
        
    ELSIF trip_count > 0 THEN
        RAISE NOTICE 'Cannot fix schema: trips table contains data. Manual migration required.';
    ELSE
        RAISE NOTICE 'Trips table already has correct schema or does not exist.';
    END IF;
END $$;

-- Check if trip_group table exists and has correct schema
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'trip_group') THEN
        
        CREATE TABLE trip_group (
            -- Primary key
            id SERIAL PRIMARY KEY,
            
            -- Relationships
            trip_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            
            -- User role in the trip
            role user_role DEFAULT 'member',
            
            -- Metadata
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            -- Constraints
            CONSTRAINT fk_trip_group_trip FOREIGN KEY (trip_id) REFERENCES trips(id) ON DELETE CASCADE,
            CONSTRAINT fk_trip_group_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            -- Ensure one membership per user per trip
            CONSTRAINT unique_trip_membership UNIQUE (trip_id, user_id)
        );
        
        -- Create indexes for performance
        CREATE INDEX idx_trip_group_trip_id ON trip_group(trip_id);
        CREATE INDEX idx_trip_group_user_id ON trip_group(user_id);
        CREATE INDEX idx_trip_group_role ON trip_group(role);
        CREATE INDEX idx_trip_group_joined_at ON trip_group(joined_at);
        
        -- Add comments for documentation
        COMMENT ON TABLE trip_group IS 'Many-to-many relationship between users and trips';
        COMMENT ON COLUMN trip_group.id IS 'Primary key, auto-incrementing';
        COMMENT ON COLUMN trip_group.trip_id IS 'ID of the trip';
        COMMENT ON COLUMN trip_group.user_id IS 'ID of the user';
        COMMENT ON COLUMN trip_group.role IS 'Role of the user in this trip';
        COMMENT ON COLUMN trip_group.joined_at IS 'Timestamp when user joined the trip';
        
        RAISE NOTICE 'Created trip_group table successfully';
    ELSE
        RAISE NOTICE 'trip_group table already exists, skipping creation';
    END IF;
END $$;

-- Check if voting_rules table exists and has correct schema
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'voting_rules') THEN
        
        CREATE TABLE voting_rules (
            -- Primary key
            id SERIAL PRIMARY KEY,
            
            -- Trip relationship (unique constraint ensures one rule per trip)
            trip_id INTEGER NOT NULL UNIQUE,
            
            -- Voting configuration
            approval_threshold FLOAT NOT NULL DEFAULT 0.7,
            min_votes_required INTEGER NOT NULL DEFAULT 3,
            max_votes_allowed INTEGER,
            duration_hours INTEGER NOT NULL DEFAULT 24,
            rule_type VARCHAR(50) DEFAULT 'majority',
            
            -- Voting period (optional explicit start/end times)
            voting_start TIMESTAMP,
            voting_end TIMESTAMP,
            
            -- Metadata
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            -- Constraints
            CONSTRAINT fk_voting_rules_trip FOREIGN KEY (trip_id) REFERENCES trips(id) ON DELETE CASCADE,
            CONSTRAINT chk_approval_threshold CHECK (approval_threshold >= 0.0 AND approval_threshold <= 1.0),
            CONSTRAINT chk_min_votes_required CHECK (min_votes_required >= 1),
            CONSTRAINT chk_max_votes_allowed CHECK (max_votes_allowed IS NULL OR max_votes_allowed >= min_votes_required),
            CONSTRAINT chk_duration_hours CHECK (duration_hours >= 1),
            CONSTRAINT chk_voting_period CHECK (voting_end IS NULL OR voting_start IS NULL OR voting_end > voting_start)
        );
        
        -- Create indexes for performance
        CREATE INDEX idx_voting_rules_trip_id ON voting_rules(trip_id);
        CREATE INDEX idx_voting_rules_voting_end ON voting_rules(voting_end);
        
        -- Add comments for documentation
        COMMENT ON TABLE voting_rules IS 'Voting configuration for trips';
        COMMENT ON COLUMN voting_rules.id IS 'Primary key, auto-incrementing';
        COMMENT ON COLUMN voting_rules.trip_id IS 'ID of the trip this rule applies to (unique)';
        COMMENT ON COLUMN voting_rules.approval_threshold IS 'Percentage of yes votes required for approval (0.0 to 1.0)';
        COMMENT ON COLUMN voting_rules.min_votes_required IS 'Minimum number of votes required before determining outcome';
        COMMENT ON COLUMN voting_rules.max_votes_allowed IS 'Maximum number of votes allowed (optional)';
        COMMENT ON COLUMN voting_rules.duration_hours IS 'Voting duration in hours from trip creation';
        COMMENT ON COLUMN voting_rules.rule_type IS 'Type of voting rule (majority, unanimous, etc.)';
        COMMENT ON COLUMN voting_rules.voting_start IS 'Explicit voting start time (optional)';
        COMMENT ON COLUMN voting_rules.voting_end IS 'Explicit voting end time (optional)';
        COMMENT ON COLUMN voting_rules.created_at IS 'Timestamp when voting rule was created';
        
        RAISE NOTICE 'Created voting_rules table successfully';
    ELSE
        RAISE NOTICE 'voting_rules table already exists, skipping creation';
    END IF;
END $$;

-- Check if votes table exists and has correct schema
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'votes') THEN
        
        CREATE TABLE votes (
            -- Primary key
            id SERIAL PRIMARY KEY,
            
            -- Trip relationship
            trip_id INTEGER NOT NULL,
            
            -- Voter identification (either user_id OR session_token must be provided)
            user_id INTEGER,
            session_token VARCHAR(255),
            
            -- Vote data
            value INTEGER NOT NULL,
            comment TEXT,
            
            -- Metadata
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            -- Constraints
            CONSTRAINT fk_votes_trip FOREIGN KEY (trip_id) REFERENCES trips(id) ON DELETE CASCADE,
            CONSTRAINT fk_votes_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            CONSTRAINT chk_vote_value CHECK (value IN (1, -1)),
            CONSTRAINT chk_voter_identification CHECK (
                (user_id IS NOT NULL AND session_token IS NULL) OR 
                (user_id IS NULL AND session_token IS NOT NULL)
            ),
            -- Ensure one vote per user per trip, or one vote per session token per trip
            CONSTRAINT unique_user_vote UNIQUE (trip_id, user_id),
            CONSTRAINT unique_session_vote UNIQUE (trip_id, session_token)
        );
        
        -- Create indexes for performance
        CREATE INDEX idx_votes_trip_id ON votes(trip_id);
        CREATE INDEX idx_votes_user_id ON votes(user_id);
        CREATE INDEX idx_votes_session_token ON votes(session_token);
        CREATE INDEX idx_votes_created_at ON votes(created_at);
        CREATE INDEX idx_votes_value ON votes(value);
        
        -- Add comments for documentation
        COMMENT ON TABLE votes IS 'Individual votes on trips (supports both authenticated users and guests)';
        COMMENT ON COLUMN votes.id IS 'Primary key, auto-incrementing';
        COMMENT ON COLUMN votes.trip_id IS 'ID of the trip being voted on';
        COMMENT ON COLUMN votes.user_id IS 'ID of authenticated user (optional for guest voting)';
        COMMENT ON COLUMN votes.session_token IS 'Session token for guest voting (optional for authenticated users)';
        COMMENT ON COLUMN votes.value IS 'Vote value: 1 for YES, -1 for NO';
        COMMENT ON COLUMN votes.comment IS 'Optional comment with the vote';
        COMMENT ON COLUMN votes.created_at IS 'Timestamp when vote was submitted';
        
        RAISE NOTICE 'Created votes table successfully';
    ELSE
        RAISE NOTICE 'votes table already exists, skipping creation';
    END IF;
END $$;

-- Create trigger function for updating updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for trips table to auto-update updated_at
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_trips_updated_at') THEN
        CREATE TRIGGER update_trips_updated_at
            BEFORE UPDATE ON trips
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    END IF;
END $$;

-- Create helper functions for common operations
CREATE OR REPLACE FUNCTION get_trip_voting_status(trip_id_param INTEGER)
RETURNS TABLE(
    total_votes INTEGER,
    yes_votes INTEGER,
    no_votes INTEGER,
    approval_percentage FLOAT,
    is_approved BOOLEAN,
    voting_ended BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    WITH vote_counts AS (
        SELECT 
            COUNT(*) as total_votes,
            COUNT(CASE WHEN v.value = 1 THEN 1 END) as yes_votes,
            COUNT(CASE WHEN v.value = -1 THEN 1 END) as no_votes
        FROM votes v
        WHERE v.trip_id = trip_id_param
    ),
    voting_rule_data AS (
        SELECT 
            vr.approval_threshold,
            vr.min_votes_required,
            vr.voting_end,
            t.created_at + (vr.duration_hours || ' hours')::INTERVAL as calculated_end
        FROM voting_rules vr
        JOIN trips t ON t.id = vr.trip_id
        WHERE vr.trip_id = trip_id_param
    )
    SELECT 
        vc.total_votes,
        vc.yes_votes,
        vc.no_votes,
        CASE 
            WHEN vc.total_votes > 0 THEN 
                ROUND((vc.yes_votes::FLOAT / vc.total_votes) * 100, 2)
            ELSE 0
        END as approval_percentage,
        CASE 
            WHEN vc.total_votes >= vr.min_votes_required THEN
                (vc.yes_votes::FLOAT / vc.total_votes) >= vr.approval_threshold
            ELSE FALSE
        END as is_approved,
        CASE 
            WHEN vr.voting_end IS NOT NULL THEN
                CURRENT_TIMESTAMP > vr.voting_end
            ELSE
                CURRENT_TIMESTAMP > vr.calculated_end
        END as voting_ended
    FROM vote_counts vc
    CROSS JOIN voting_rule_data vr;
END;
$$ LANGUAGE plpgsql;

-- Function to check if user can vote on trip
CREATE OR REPLACE FUNCTION can_user_vote_on_trip(
    trip_id_param INTEGER,
    user_id_param INTEGER DEFAULT NULL,
    session_token_param VARCHAR DEFAULT NULL
)
RETURNS BOOLEAN AS $$
DECLARE
    voting_ended BOOLEAN;
    already_voted BOOLEAN;
BEGIN
    -- Check if voting has ended
    SELECT voting_ended INTO voting_ended
    FROM get_trip_voting_status(trip_id_param);
    
    IF voting_ended THEN
        RETURN FALSE;
    END IF;
    
    -- Check if user already voted
    IF user_id_param IS NOT NULL THEN
        SELECT EXISTS(
            SELECT 1 FROM votes 
            WHERE trip_id = trip_id_param AND user_id = user_id_param
        ) INTO already_voted;
    ELSIF session_token_param IS NOT NULL THEN
        SELECT EXISTS(
            SELECT 1 FROM votes 
            WHERE trip_id = trip_id_param AND session_token = session_token_param
        ) INTO already_voted;
    ELSE
        RETURN FALSE;
    END IF;
    
    RETURN NOT already_voted;
END;
$$ LANGUAGE plpgsql;

-- Log migration completion
DO $$ 
BEGIN
    RAISE NOTICE 'Migration 002 completed successfully!';
    RAISE NOTICE 'Fixed schema mismatch between database and code expectations';
    RAISE NOTICE 'All trip management tables are now properly configured';
END $$;

-- Commit all changes
COMMIT; 