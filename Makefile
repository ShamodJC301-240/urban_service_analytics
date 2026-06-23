# Python interpreter inside venv
PYTHON = venv/bin/python3

# Uvicorn inside venv
UVICORN = venv/bin/uvicorn


# Install dependencies
install:
	$(PYTHON) -m pip install -r requirements.txt


# Create database
create-db:
	createdb urban_service_analytics


# Setup schema + views
setup-db: create-db
	psql -d urban_service_analytics -f sql/schema.sql
	psql -d urban_service_analytics -f sql/views.sql


# ETL ingest
ingest:
	$(PYTHON) backend/etl/ingest_311_data.py


# Start API server
server:
	PYTHONPATH=backend $(UVICORN) app.main:app --reload --reload-dir backend


# First-time setup
init: install setup-db


# Full run
run:
	make ingest && make server