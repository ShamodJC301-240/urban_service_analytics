# FastAPI route definitions for our 311 analytics API.
# Each endpoint queries one of the views defined in views.sql and returns the results as JSON.
# Router is registered in main.py via app.include_router(router).

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.db import get_db

router = APIRouter(
    prefix="/api",   # all routes start with /api/...
    tags=["311 Analytics"],
)



# Helper
# ------------

def query_view(db: Session, sql: str) -> list[dict]:
    """Execute a SQL string and return rows as a list of dicts."""
    try:
        result = db.execute(text(sql))
        
        # mappings() converts each row to a dict keyed by column name
        return [dict(row) for row in result.mappings()]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Requests by Borough
# Returns total request count per borough. Sorted descending.
# sorted by volume descending.
# ─────────────────────────────────────────────

@router.get(
    "/requests/by-borough",
    summary="Total requests per borough",
    response_description="List of boroughs with request counts",
)
def requests_by_borough(db: Session = Depends(get_db)):
    """
    Returns total 311 request counts grouped by borough,
    ordered from highest to lowest volume.
    """
    return query_view(db, "SELECT * FROM vw_requests_by_borough")



# Top Complaints
# Returns the top 5 complaint types
# --------------------------------------------------

@router.get(
    "/complaints/top",
    summary="Top 5 complaint types by volume",
    response_description="List of complaint types with request counts",
)
def top_complaints(db: Session = Depends(get_db)):
    limit: int = 5,
    """
    Returns the 5 most common complaint types across all boroughs.
    Useful for a bar chart or ranked list on a dashboard.
    """
    return query_view(db, "SELECT * FROM vw_top_complaints")




# Returns a two-row breakdown: Open and Closed counts.
# -----------------------------------------------------
@router.get(
    "/requests/status",
    summary="Open vs closed request counts",
    response_description="Open and closed request totals",
)
def open_vs_closed(db: Session = Depends(get_db)):
    """
    Returns total request counts split by open/closed status.
    A request is 'Open' if it has no closed_date.
    """
    return query_view(db, "SELECT * FROM vw_open_vs_closed")




# Returns decimal ratios for open and closed (ratios add up to to 1).
# ----------------------------------------------------------------------
@router.get(
    "/requests/status/ratio",
    summary="Open vs closed ratio",
    response_description="Decimal ratio of open and closed requests",
)
def open_closed_ratio(db: Session = Depends(get_db)):
    """
    Returns the proportion of requests that are open and closed
    as decimals (e.g. open_ratio: 0.312, closed_ratio: 0.688).
    """
    return query_view(db, "SELECT * FROM vw_open_closed_ratio")



# Returns Average Resolution Time
# ---------------------------------
@router.get(
    "/requests/resolution-time",
    summary="Average resolution time in hours",
    response_description="Mean hours from creation to close",
)
def avg_resolution_time(db: Session = Depends(get_db)):
    """
    Returns the average time (in hours) to resolve a 311 request.
    Only includes closed requests with valid timestamps.
    """
    return query_view(db, "SELECT * FROM vw_avg_resolution_time")



# Resolution Time By Borough And Complaint Type
# -------------------------------------------------

@router.get(
    "/requests/resolution-time/breakdown",
    summary="Resolution time by borough and complaint type",
    response_description="Avg resolution hours per borough/complaint combination",
)
def resolution_time_breakdown(
    borough: str | None = None,
    complaint_type: str | None = None,
    db: Session = Depends(get_db),
):
    """
    Returns average resolution time broken down by borough and
    complaint type, ordered slowest first.

    Optional query parameters:
    - **borough**: filter to a single borough (e.g. BROOKLYN)
    - **complaint_type**: filter to a single complaint type
    """
    # Build the WHERE clause dynamically based on provided filters.
    # Using parameterised queries via SQLAlchemy text() to prevent SQL injection.
    filters = []
    params = {}

    if borough:
        filters.append("borough = :borough")
        params["borough"] = borough.upper()

    if complaint_type:
        filters.append("complaint_type = :complaint_type")
        params["complaint_type"] = complaint_type

    sql = "SELECT * FROM vw_resolution_by_borough_complaint"
    if filters:
        sql += " WHERE " + " AND ".join(filters)

    try:
        result = db.execute(text(sql), params)
        return [dict(row) for row in result.mappings()]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# Daily Request Trends
# --------------------------

@router.get(
    "/requests/trends/daily",
    summary="Daily request volume over time",
    response_description="Request counts per calendar day",
)
def daily_trends(
    start_date: str | None = None,
    end_date: str | None = None,
    db: Session = Depends(get_db),
):
    """
    Returns total 311 requests per day, ordered chronologically.
    Use this to power a time-series line chart.

    Optional query parameters:
    - **start_date**: earliest date to include (YYYY-MM-DD)
    - **end_date**: latest date to include (YYYY-MM-DD)
    """
    filters = []
    params = {}

    if start_date:
        filters.append("request_day >= :start_date")
        params["start_date"] = start_date

    if end_date:
        filters.append("request_day <= :end_date")
        params["end_date"] = end_date

    sql = "SELECT * FROM vw_daily_request_trends"
    if filters:
        sql += " WHERE " + " AND ".join(filters)

    try:
        result = db.execute(text(sql), params)
        return [dict(row) for row in result.mappings()]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# 7-Day Rolling Average Trends
# ----------------------------------------

@router.get(
    "/requests/trends/rolling",
    summary="Daily request volume with 7-day rolling average",
    response_description="Daily counts plus smoothed 7-day average",
)
def rolling_trends(db: Session = Depends(get_db)):
    """
    Returns daily request counts alongside a 7-day trailing average.
    Useful for smoothing out weekday/weekend spikes in line charts.
    """
    return query_view(db, "SELECT * FROM vw_daily_request_trends_rolling")



# Backlog age
# Buckets currently open requests by how long they've been open.
# -------------------------------------------------------------------

@router.get(
    "/requests/backlog/aging",
    summary="Open request backlog by age",
    response_description="Open request counts bucketed by age range",
)
def backlog_aging(db: Session = Depends(get_db)):
    """
    Returns open requests grouped into age buckets:
    0–7 days, 8–30 days, 31–90 days, 90+ days.
    Shows how stale the backlog is, not just how large.
    """
    return query_view(db, "SELECT * FROM vw_open_backlog_aging")
