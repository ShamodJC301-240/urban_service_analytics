-- ad-hoc queries for 311 data validation and exploration
-- all reusable reporting logic lives in views.sql
-- this file is safe to run anytime (read-only queries only)

-- 1. basic data checks
-- --------------------

-- total records in staging table
SELECT COUNT(*) AS total_requests
FROM stg_311_requests;

-- quick sample for schema validation
SELECT *
FROM stg_311_requests
LIMIT 10;

-- null checks for key fields
SELECT
    COUNT(*) FILTER (WHERE borough IS NULL)        AS null_boroughs,
    COUNT(*) FILTER (WHERE complaint_type IS NULL) AS null_complaint_types,
    COUNT(*) FILTER (WHERE created_date IS NULL)   AS null_created_dates,
    COUNT(*) FILTER (WHERE unique_key IS NULL)     AS null_unique_keys
FROM stg_311_requests;


-- 2. core kpis
-- ------------

-- open vs closed requests
SELECT
    CASE WHEN closed_date IS NULL THEN 'Open' ELSE 'Closed' END AS status,
    COUNT(*) AS total_requests
FROM stg_311_requests
GROUP BY 1;

-- open ratio (share of unresolved requests)
SELECT
    ROUND(
        COUNT(*) FILTER (WHERE closed_date IS NULL)::decimal
        / NULLIF(COUNT(*), 0),
        3
    ) AS open_ratio
FROM stg_311_requests;

-- average resolution time (hours)
-- excludes invalid timestamps
SELECT
    ROUND(
        AVG(EXTRACT(EPOCH FROM (closed_date - created_date)) / 3600)::numeric,
        2
    ) AS avg_resolution_hours
FROM stg_311_requests
WHERE closed_date IS NOT NULL
  AND created_date IS NOT NULL
  AND closed_date > created_date;


-- 3. data quality checks
-- ---------------------

-- bad timestamp rows (data errors)
SELECT COUNT(*) AS bad_timestamp_rows
FROM stg_311_requests
WHERE closed_date IS NOT NULL
  AND closed_date < created_date;

-- borough distribution (check consistency)
SELECT borough, COUNT(*) AS total
FROM stg_311_requests
GROUP BY borough
ORDER BY total DESC;

-- status distribution (detect unexpected values)
SELECT status, COUNT(*) AS total
FROM stg_311_requests
GROUP BY status
ORDER BY total DESC;


-- 4. deeper analysis
-- ------------------

-- complaint types with longest resolution times
SELECT
    complaint_type,
    COUNT(*) AS closed_requests,
    ROUND(
        AVG(EXTRACT(EPOCH FROM (closed_date - created_date)) / 3600)::numeric,
        1
    ) AS avg_resolution_hours
FROM stg_311_requests
WHERE closed_date > created_date
  AND complaint_type IS NOT NULL
GROUP BY complaint_type
ORDER BY avg_resolution_hours DESC
LIMIT 20;

-- borough backlog intensity (open share)
SELECT
    borough,
    COUNT(*) AS total_requests,
    COUNT(*) FILTER (WHERE closed_date IS NULL) AS open_requests,
    ROUND(
        COUNT(*) FILTER (WHERE closed_date IS NULL)::decimal
        / NULLIF(COUNT(*), 0),
        3
    ) AS open_ratio
FROM stg_311_requests
WHERE borough IS NOT NULL
GROUP BY borough
ORDER BY open_ratio DESC;

-- volume by day of week
SELECT
    TO_CHAR(created_date, 'Day') AS day_of_week,
    EXTRACT(DOW FROM created_date)::int AS dow_num,
    COUNT(*) AS total_requests
FROM stg_311_requests
WHERE created_date IS NOT NULL
GROUP BY day_of_week, dow_num
ORDER BY dow_num;

-- agency workload + closure rate
SELECT
    agency_name,
    COUNT(*) AS total_requests,
    COUNT(*) FILTER (WHERE closed_date IS NOT NULL) AS closed_requests,
    ROUND(
        COUNT(*) FILTER (WHERE closed_date IS NOT NULL)::decimal
        / NULLIF(COUNT(*), 0),
        3
    ) AS closure_rate
FROM stg_311_requests
WHERE agency_name IS NOT NULL
GROUP BY agency_name
ORDER BY total_requests DESC
LIMIT 15;

-- open backlog aging buckets
SELECT
    CASE
        WHEN age_days <= 7 THEN '0–7 days'
        WHEN age_days <= 30 THEN '8–30 days'
        WHEN age_days <= 90 THEN '31–90 days'
        ELSE '90+ days'
    END AS age_bucket,
    COUNT(*) AS open_requests
FROM (
    SELECT EXTRACT(DAY FROM NOW() - created_date)::int AS age_days
    FROM stg_311_requests
    WHERE closed_date IS NULL
      AND created_date IS NOT NULL
) aged
GROUP BY age_bucket
ORDER BY MIN(aged.age_days);