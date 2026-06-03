
-- Drop staging table if it already exists
DROP TABLE IF EXISTS stg_311_requests;

-- Raw API ingestion table
CREATE TABLE stg_311_requests (
    unique_key BIGINT PRIMARY KEY,
    created_date TIMESTAMP,
    closed_date TIMESTAMP,
    agency VARCHAR(20),
    agency_name TEXT,
    complaint_type TEXT,
    descriptor TEXT,
    borough VARCHAR(20),
    status VARCHAR(50),
    latitude NUMERIC,
    longitude NUMERIC
);