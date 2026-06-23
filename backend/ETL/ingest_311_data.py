"""
 ETL script for nyc 311 service request data.
 pulls data from the nyc open data api in batches, cleans it,
 and loads it into the postgres staging table (stg_311_requests).
"""
# all configuration lives in .env file. See .env.example for required variables.


import logging
import os

import pandas as pd
import requests
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from sqlalchemy import create_engine, text
from urllib3.util.retry import Retry
from pathlib import Path

# Explicitly load .env from the project root
# ----------------------------------------------
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")


# logging
# --------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)



# configuration
# load environment variables from .env file.
# --------------------------------------------------------------

load_dotenv()

API_URL = os.getenv("NYC_311_API_URL")
API_LIMIT = int(os.getenv("API_LIMIT", 1000))
MAX_BATCHES = int(os.getenv("MAX_BATCHES", 5))

"""
Columns we actually care about from the api response.
We explicitly define this so we don’t accidentally load unexpected fields
if the api changes or adds new columns.
"""

KEEP_COLS = [
    "unique_key",
    "created_date",
    "closed_date",
    "agency",
    "agency_name",
    "complaint_type",
    "descriptor",
    "borough",
    "incident_zip",
    "status",
    "latitude",
    "longitude",
]

# text fields that need cleaning (strip whitespace + normalize nulls)
TEXT_COLS = [
    "agency",
    "agency_name",
    "complaint_type",
    "descriptor",
    "borough",
    "status",
    "incident_zip",
]



# database connection
# creates a sqlalchemy engine using environment variables.
# ----------------------------------------------------------

def get_engine():
    """build postgres sqlalchemy engine from environment variables."""

    required = ["DB_HOST", "DB_NAME", "DB_USER", "DB_PORT", "DB_PASSWORD"]
    missing = [v for v in required if not os.getenv(v)]

    if missing:
        raise EnvironmentError(
            f"missing required environment variables: {missing}"
        )

    return create_engine(
        f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )



# fetch
# pulls data from nyc 311 api using pagination.
# includes retry logic so temporary api failures don’t crash the pipeline.
# ---------------------------------------------------------------------------

def fetch_data(api_url: str, limit: int, max_batches: int) -> list[dict]:
    """fetch raw 311 records from nyc open data api."""

    if not api_url:
        raise ValueError("nyc_311_api_url is not set.")

    session = requests.Session()

    retry = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )

    session.mount("https://", HTTPAdapter(max_retries=retry))

    rows = []
    offset = 0

    for batch_num in range(max_batches):
        log.info("fetching batch %d (offset=%d)", batch_num + 1, offset)

        response = session.get(
            api_url,
            params={
                "$limit": limit,
                "$offset": offset,
                "$order": "created_date desc",
            },
            timeout=30,
        )

        response.raise_for_status()
        data = response.json()

        if not data:
            log.info("no more data returned — stopping early.")
            break

        rows.extend(data)
        offset += limit

    log.info("fetched %d total records", len(rows))
    return rows



# clean
# standardizes raw api data into a consistent dataframe.
# this ensures downstream sql queries behave correctly.
# ---------------------------------------------------------------

def clean_data(rows: list[dict]) -> pd.DataFrame:

    df = pd.DataFrame(rows)

    if df.empty:
        raise ValueError("no data returned from api.")

    # keep only known columns
    available = [c for c in KEEP_COLS if c in df.columns]
    df = df[available]

    # convert data types safely (bad values become nan instead of crashing)
    if "unique_key" in df:
        df["unique_key"] = pd.to_numeric(df["unique_key"], errors="coerce")

    if "created_date" in df:
        df["created_date"] = pd.to_datetime(df["created_date"], errors="coerce")

    if "closed_date" in df:
        df["closed_date"] = pd.to_datetime(df["closed_date"], errors="coerce")

    if "latitude" in df:
        df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")

    if "longitude" in df:
        df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")

    # clean text fields (strip whitespace, normalize nulls)
    for col in TEXT_COLS:
        if col in df:
            df[col] = df[col].astype(str).str.strip()
            df[col] = df[col].replace({"": None, "nan": None})

    # standardize borough formatting
    if "borough" in df:
        df["borough"] = df["borough"].str.upper()

    # remove invalid primary keys
    null_keys = df["unique_key"].isna().sum()
    if null_keys > 0:
        log.warning("dropping %d invalid rows (missing unique_key)", null_keys)

    df = df[df["unique_key"].notna()]

    # remove duplicates from overlapping api batches
    df = df.drop_duplicates(subset=["unique_key"])

    # reorder columns for consistency with db schema
    df = df[[c for c in KEEP_COLS if c in df.columns]]

    log.info("clean complete — %d rows ready", len(df))
    return df



# load
# writes cleaned data into postgres staging table.
# uses truncate + insert to keep schema intact.
# ─────────────────────────────────────────────

def load_to_postgres(df: pd.DataFrame, engine) -> None:

    log.info("truncating staging table...")

    with engine.begin() as conn:
        conn.execute(text("truncate table stg_311_requests"))

    log.info("loading %d rows into postgres...", len(df))

    df.to_sql(
        "stg_311_requests",
        engine,
        if_exists="append",
        index=False,
        method="multi",
    )

    log.info("load complete.")



# entry point
# runs full etl pipeline in order:
# ------------------------------------------

if __name__ == "__main__":
    engine = get_engine()
    rows = fetch_data(API_URL, API_LIMIT, MAX_BATCHES)
    df = clean_data(rows)
    load_to_postgres(df, engine)

    log.info("=" * 40)
    log.info("311 etl complete")
    log.info("rows loaded: %d", len(df))
    log.info("=" * 40)