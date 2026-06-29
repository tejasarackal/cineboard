# CineBoard

A small ELT pipeline for movie data. It pulls from the TMDB API, loads the raw
responses into Snowflake, transforms them with dbt, and shows a few insights in a
Streamlit app. Airflow runs the whole thing.

## Stack

- Python 3.11
- Airflow (Astronomer runtime) for orchestration
- dbt on Snowflake, run from Airflow via Cosmos
- Snowflake for storage
- Streamlit for the dashboard

## What it does

1. Extract: get movies from the TMDB discover endpoint, then fan out to
   `/movie/{id}` and `/movie/{id}/credits` to pick up budget, revenue, runtime,
   cast and crew.
2. Load: land the raw JSON payloads into Snowflake as VARIANT.
3. Transform: dbt builds staging -> intermediate -> marts. Two fact tables
   (one row per movie, and a daily snapshot per movie), dimensions for genre,
   person and company, bridge tables for the many-to-many links, and a few
   aggregate tables that the dashboard reads.
4. Serve: Streamlit queries the marts and renders five views (genre ROI,
   bankable talent, budget vs outcome, genre popularity over time, and trending).

## Running it

You need Docker, the Astro CLI, a TMDB API key, and a Snowflake account.

Set up Snowflake once:

```sql
create database if not exists tesla_raw_db;
create database if not exists tesla_staging_db;
create database if not exists tesla_analytics_db;
create schema if not exists tesla_raw_db.tmdb;

create table if not exists tesla_raw_db.tmdb.raw_movies        (raw_payload variant, ingested_at timestamp_ntz default current_timestamp());
create table if not exists tesla_raw_db.tmdb.raw_movie_details (raw_payload variant, ingested_at timestamp_ntz default current_timestamp());
create table if not exists tesla_raw_db.tmdb.raw_credits       (raw_payload variant, ingested_at timestamp_ntz default current_timestamp());
create stage if not exists tesla_raw_db.tmdb.api_payload;
```

Start Airflow:

```bash
astro dev start
```

In the Airflow UI (http://localhost:8080, admin/admin) add:

- a Variable `tmdb_api_key` with your TMDB key
- a Connection `snowflake_conn` (type Snowflake) with your account, user,
  password, role, warehouse and database

Trigger the `tmdb_ingestion_pipeline` DAG. It extracts, loads, and then runs the
dbt models and tests.

Run the dashboard:

```bash
cd app
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# add your Snowflake creds to app/.streamlit/secrets.toml first
streamlit run streamlit_app.py
```

## Layout

```
dags/        Airflow DAG and the dbt project (dags/dbt/data_pipeline)
include/     TMDB API client used by the DAG
app/         Streamlit dashboard
tools/       one-off TMDB profiling script
```

## Notes

- A budget or revenue of 0 means "unknown" in TMDB, so those are set to NULL and
  left out of ROI math.
- `fact_movie` is one row per movie. `fact_movie_snapshot` is one row per movie
  per day, for tracking popularity and votes over time. On a fresh build the
  snapshot history is seeded with synthetic dates (flagged `is_synthetic`) so the
  trend chart has something to show; real history accrues as the DAG runs.
- Re-runs are idempotent. Staging deduplicates on the TMDB id and the facts
  upsert on it.
- Cast is capped at the top 10 by popularity per movie; crew is filtered to
  directors only.
