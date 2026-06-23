# urban_service_analytics

Building a full-stack data pipeline and REST API for analyzing NYC 311 service request data. Fetches live data from the NYC Open Data API, loads it into PostgreSQL, and exposes KPI metrics through a FastAPI backend. Ready to connect to Power BI or a custom dashboard.


### What It Does

- Pulls 311 service request data from the NYC Open Data API in paginated batches
- Cleans and loads the data into a PostgreSQL staging table
- Computes KPIs through SQL views (borough breakdowns, complaint types, resolution times, backlog aging)
- Serves the data through a REST API built with FastAPI
- Auto-generates interactive API documentation at /docs
