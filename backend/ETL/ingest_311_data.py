import os
import requests
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine

#Loading our environment variables
load_dotenv()

API_URL = os.getenv("NYC_311_API_URL")
API_LIMIT = int(os.getenv("API_LIMIT", 1000))
MAX_BATCHES = int(os.getenv("MAX_BATCHES", 5))

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PORT = os.getenv("DB_PORT")
DB_PASSWORD = os.getenv("DB_PASSWORD")

 
# Build Postgres connection
 
engine = create_engine(
    f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

 
# Paginated API ingestion within limit of 1000 as per NYC Open Data site
 
rows = []
offset = 0

for i in range(MAX_BATCHES):
    print(f"Fetching batch {i + 1}")

    response = requests.get(API_URL, params={
        "$limit": API_LIMIT,
        "$offset": offset,
        "$order": "created_date DESC"
    })

    data = response.json()

    if not data:
        break

    rows.extend(data)
    offset += API_LIMIT


# Converting rows to DataFrame

df = pd.DataFrame(rows)


# Select only useful columns

keep_cols = [
    "unique_key",
    "created_date",
    "closed_date",
    "complaint_type",
    "descriptor",
    "borough",
    "incident_zip",
    "status",
    "agency",
    "latitude",
    "longitude"
]

available_cols = [col for col in keep_cols if col in df.columns]

df = df[available_cols]


# Load data into Postgres 
df.to_sql(
    "stg_311_requests",
    engine,
    if_exists="replace",
    index=False
)

print(f"Data ingested and sent to postgres. Here are our number of rows {len(df)}")