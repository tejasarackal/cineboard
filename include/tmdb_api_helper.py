#!/usr/bin/env python3
"""
tmdb_api_helper.py — data-profiling pass over a TMDB sample (run BEFORE finalizing the model)

Inputs  : env TMDB_API_KEY ; optional --years (e.g. 2018-2023), --pages, --sample
Outputs : prints a summary and writes ../docs/profile_report.md.
Run     : TMDB_API_KEY=xxx python3 tools/profile_tmdb.py --years 2018-2023 --pages 2 --sample 150
Notes   : stdlib only (urllib) so it runs with zero install. Hits the live TMDB API — run it
          locally where you have network + a free key (themoviedb.org). 
Last updated: 2026-06-26
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from airflow.sdk import Variable

BASE = "https://api.themoviedb.org/3"

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
            if e.code == 429: 
                time.sleep(2 * (attempt + 1))
                continue
            raise
        except urllib.error.URLError as e:
            last_err = e
            time.sleep(1 * (attempt + 1))
    raise RuntimeError(f"failed after retries ({last_err}): {url}")


def discover(year: int, page: int) -> dict:
    return get("/discover/movie", primary_release_year=year, sort_by="popularity.desc", page=page)


def details(movie_id: int) -> dict:
    return get(f"/movie/{movie_id}")


def credits(movie_id: int) -> dict:
    return get(f"/movie/{movie_id}/credits")

