# FastAPI application entry point for the Urban Service Analytics API.
# Run locally with uvicorn main:app --reload inside the terminal

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.db import check_db_connection
from backend.app.routers import router


# Startup message
# Prints the local server links to the terminal every time the server starts.
# -----------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n" + "=" * 40)
    print("  Urban Service Analytics API")
    print("http://localhost:8000")
    print(f"Here are our docs http://localhost:8000/docs")
    print(f"Here is the health of our server http://localhost:8000/health")
    print("=" * 40 + "\n")
    yield


# App
# --------------------

app = FastAPI(
    title="Urban Service Analytics",
    description=(
        "REST API for exploring NYC 311 service request data. "
        "Exposes KPI views for borough breakdowns, complaint types, "
        "resolution times, daily trends, and backlog aging."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


# CORS or Cross Origin Resource Sharing.
# Allows the frontend to call this API from a browser.
# ----------------------------------------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


# All API endpoints are defined in routers.py.
# -----------------------------------------------

app.include_router(router)


# Root. Entry point for our API
# -----------------------------------

@app.get("/", tags=["Meta"])
def root():
    return {
        "service": "Urban Service Analytics API",
        "version": "1.0.0",
        "docs": "/docs",
    }


# Health Check
# Endpoint for monitoring and deployment checks.
# ------------------------------------------------

@app.get("/health", tags=["Meta"])
def health():
    db_ok = check_db_connection()
    return {
        "status": "ok" if db_ok else "degraded",
        "database": "connected" if db_ok else "unreachable",
    }