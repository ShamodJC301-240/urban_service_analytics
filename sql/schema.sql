-- schema for 311 staging table
-- run once before first ingest
-- drop cascade allows safe rebuild during development (remove in prod)

DROP TABLE IF EXISTS stg_311_requests CASCADE;

CREATE TABLE stg_311_requests (

    -- primary key from nyc 311 system
    unique_key      BIGINT PRIMARY KEY,

    -- request creation timestamp (required for all time-based analysis)
    created_date    TIMESTAMP NOT NULL,

    -- closure timestamp (null = still open)
    closed_date     TIMESTAMP,

    -- agency short code (e.g. NYPD, DEP)
    agency          VARCHAR(20),

    -- full agency name
    agency_name     TEXT,

    -- complaint category
    complaint_type  TEXT,

    -- complaint sub-category
    descriptor      TEXT,

    -- borough (standardized to uppercase during ingest)
    borough         VARCHAR(20),

    -- zip code (varchar preserves leading zeros and edge cases)
    incident_zip    VARCHAR(10),

    -- request status (open, closed, etc.)
    status          VARCHAR(50),

    -- geolocation for mapping
    latitude        NUMERIC(10,7),
    longitude       NUMERIC(10,7)
);

-- indexes for common analytics queries

CREATE INDEX idx_stg_311_borough
    ON stg_311_requests (borough);

CREATE INDEX idx_stg_311_complaint_type
    ON stg_311_requests (complaint_type);

CREATE INDEX idx_stg_311_created_date
    ON stg_311_requests (created_date);

CREATE INDEX idx_stg_311_closed_date
    ON stg_311_requests (closed_date);