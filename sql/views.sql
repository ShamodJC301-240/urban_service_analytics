-- views for 311 analytics project
-- all reusable reporting logic lives here
-- kpi_queries.sql contains only ad-hoc analysis (no schema changes)

-- 1. requests by borough
-- ----------------------

CREATE OR REPLACE VIEW vw_requests_by_borough AS
SELECT
    borough,
    COUNT(*) AS total_requests
FROM stg_311_requests
WHERE borough IS NOT NULL
GROUP BY borough
ORDER BY total_requests DESC;


-- 2. top complaint types
-- ----------------------

CREATE OR REPLACE VIEW vw_top_complaints AS
SELECT
    complaint_type,
    COUNT(*) AS total_requests
FROM stg_311_requests
WHERE complaint_type IS NOT NULL
GROUP BY complaint_type
ORDER BY total_requests DESC
LIMIT 5;


-- 3. open vs closed requests
-- --------------------------

CREATE OR REPLACE VIEW vw_open_vs_closed AS
SELECT
    CASE
        WHEN closed_date IS NULL THEN 'Open'
        ELSE 'Closed'
    END AS status,
    COUNT(*) AS total_requests
FROM stg_311_requests
GROUP BY 1;


-- 4. open / closed ratio
-- ----------------------

CREATE OR REPLACE VIEW vw_open_closed_ratio AS
SELECT
    ROUND(
        COUNT(*) FILTER (WHERE closed_date IS NULL)::decimal
        / NULLIF(COUNT(*), 0),
        3
    ) AS open_ratio,
    ROUND(
        COUNT(*) FILTER (WHERE closed_date IS NOT NULL)::decimal
        / NULLIF(COUNT(*), 0),
        3
    ) AS closed_ratio
FROM stg_311_requests;


-- 5. average resolution time
-- --------------------------
-- excludes invalid timestamps (closed < created)

CREATE OR REPLACE VIEW vw_avg_resolution_time AS
SELECT
    ROUND(
        AVG(EXTRACT(EPOCH FROM (closed_date - created_date)) / 3600)::numeric,
        2
    ) AS avg_resolution_hours
FROM stg_311_requests
WHERE closed_date IS NOT NULL
  AND created_date IS NOT NULL
  AND closed_date > created_date;


-- 6. daily request trends
-- -----------------------

CREATE OR REPLACE VIEW vw_daily_request_trends AS
SELECT
    DATE(created_date) AS request_day,
    COUNT(*) AS total_requests
FROM stg_311_requests
WHERE created_date IS NOT NULL
GROUP BY DATE(created_date)
ORDER BY request_day;


-- 7. 7-day rolling trend
-- ----------------------

CREATE OR REPLACE VIEW vw_daily_request_trends_rolling AS
SELECT
    request_day,
    total_requests,
    ROUND(
        AVG(total_requests) OVER (
            ORDER BY request_day
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        )::numeric,
        1
    ) AS rolling_7_day_avg
FROM (
    SELECT
        DATE(created_date) AS request_day,
        COUNT(*) AS total_requests
    FROM stg_311_requests
    WHERE created_date IS NOT NULL
    GROUP BY DATE(created_date)
) daily;


-- 8. resolution time by borough and complaint type
-- -------------------------------------------------

CREATE OR REPLACE VIEW vw_resolution_by_borough_complaint AS
SELECT
    borough,
    complaint_type,
    COUNT(*) AS closed_requests,
    ROUND(
        AVG(EXTRACT(EPOCH FROM (closed_date - created_date)) / 3600)::numeric,
        1
    ) AS avg_resolution_hours
FROM stg_311_requests
WHERE closed_date IS NOT NULL
  AND created_date IS NOT NULL
  AND closed_date > created_date
  AND borough IS NOT NULL
  AND complaint_type IS NOT NULL
GROUP BY borough, complaint_type
ORDER BY avg_resolution_hours DESC;


-- 9. open backlog aging
-- ---------------------

CREATE OR REPLACE VIEW vw_open_backlog_aging AS
SELECT
    CASE
        WHEN age_days <= 7 THEN '0–7 days'
        WHEN age_days <= 30 THEN '8–30 days'
        WHEN age_days <= 90 THEN '31–90 days'
        ELSE '90+ days'
    END AS age_bucket,
    COUNT(*) AS open_requests
FROM (
    SELECT
        EXTRACT(DAY FROM NOW() - created_date)::int AS age_days
    FROM stg_311_requests
    WHERE closed_date IS NULL
      AND created_date IS NOT NULL
) aged
GROUP BY age_bucket
ORDER BY MIN(aged.age_days);