# Database connection and session management. 
# This is where we connect to to Postgres.

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()

# Engine
# --------------------------------------
def get_engine():
    """
    Builds an SQLAlchemy engine from our environment variables.

    Raises an EnvironmentError if any required DB environment variables are missing.
    """
    required = ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]
    missing = [v for v in required if not os.getenv(v)]
    if missing:
        raise EnvironmentError(
            f"Missing required environment variables: {missing}\n"
            "Add them to your .env file or set them in your environment."
        )

    return create_engine(
        f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}",
        # pool_pre_ping checks the connection is alive before using it.
        # Prevents "connection closed" errors after periods of inactivity.
        pool_pre_ping=True,
    )


# Creates session once when the module is first imported and reused across requests.
# ---------------------------------------------------------------------------------------
engine = get_engine()
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


# Session Dependency
# ----------------------
def get_db():
    """
    FastAPI dependency that provides a database session per request.
    Yields a session, then closes it when the request is done
    whether it succeeded or raised an exception.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Called by health check endpoint to let us know if our database is running correctly
# ---------------------------------------------------------------------------------------

def check_db_connection() -> bool:
    """Return True if the database is reachable, False otherwise."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
