-- Requests by borough
-- Avg resolution time
-- Open vs closed ratio
-- Top 5 complaint types
-- Daily request trends

-- Getting the number of records from our api pull
SELECT COUNT(*) AS total_content 
FROM stg_311_requests;

-- Selecting records for inspection pull (10) records
SELECT *
FROM stg_311_requests
LIMIT 10;

-- Fetching total requests and divying them up by borough
SELECT borough, COUNT(*) AS total_requests
FROM stg_311_requests
GROUP BY borough
ORDER BY total_requests DESC;

-- Getting top complaints
SELECT complaint_type, COUNT(*) AS total_requests
FROM stg_311_requests
GROUP BY complaint_type
ORDER BY total_requests DESC
LIMIT 10;

-- SQL test run
-- Got this error when running: ERROR:  relation "vw_requests_by_borough" already exists So I am adding a REPLACE to query

CREATE OR REPLACE VIEW vw_requests_by_borough AS
SELECT borough, COUNT(*) AS total_requests
FROM stg_311_requests
GROUP BY borough;

