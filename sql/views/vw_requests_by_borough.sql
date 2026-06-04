-- creating view of requests by borough

CREATE OR REPLACE VIEW vw_requests_by_borough AS
SELECT borough, COUNT(*) AS total_requests
FROM stg_311_requests
GROUP BY borough;