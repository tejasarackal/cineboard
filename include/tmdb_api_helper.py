"""
tmdb_api_helper.py - thin TMDB API client (auth + retry/backoff) for the ingestion DAG.

Purpose : GET TMDB endpoints with authentication and rate-limit handling; shared by the
          extract tasks in dags/tmdb_ingestion_dag.py.
Inputs  : TMDB key from Airflow Variable 'tmdb_api_key' (or env TMDB_API_KEY).
Outputs : parsed JSON (dict) from the TMDB endpoint.
Exports : get(path, **params), discover(year, page), details(movie_id), credits(movie_id).
Last updated: 2026-06-28
"""
from __future__ import annotations

import json
import logging
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from airflow.sdk import Variable

BASE = "https://api.themoviedb.org/3"

log = logging.getLogger("airflow.task")

def _api_key() -> str:
    key = os.environ.get("TMDB_API_KEY") or Variable.get("tmdb_api_key")
    if not key:
        raise RuntimeError("TMDB_API_KEY is not set in Airflow Variables. set env TMDB_API_KEY or Variable 'tmdb_api_key'")
    return key

def get(path: str, **params) -> dict:
    """GET a TMDB endpoint with authentication"""
    key = _api_key()
    headers: dict[str, str] = {}
    if key.startswith("eyJ"):  
        headers["Authorization"] = f"Bearer {key}"
    else:
        params["api_key"] = key
    url = f"{BASE}{path}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers=headers)
    last_err: Exception | None = None
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            last_err = e
            if e.code == 429:  # rate limited -> back off and retry
                log.warning("TMDB 429 on %s, retry %s/5", path, attempt + 1)
                time.sleep(2 * (attempt + 1))
                continue
            raise
        except urllib.error.URLError as e:
            last_err = e
            log.warning("TMDB connection error on %s, retry %s/5", path, attempt + 1)
            time.sleep(1 * (attempt + 1))
    raise RuntimeError(f"failed after retries ({last_err}): {path}")


def discover(year: int, page: int) -> dict:
    return get("/discover/movie", primary_release_year=year, sort_by="popularity.desc", page=page)


def details(movie_id: int) -> dict:
    return get(f"/movie/{movie_id}")


def credits(movie_id: int) -> dict:
    return get(f"/movie/{movie_id}/credits")

