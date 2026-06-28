#!/usr/bin/env python3
"""
profile_tmdb.py — data-profiling pass over a TMDB sample (run BEFORE finalizing the model).

Purpose : Pull a representative sample (discover by release year + fan out to /movie and
          /credits) and report coverage so the data model is grounded in what the API
          actually returns — null/zero rates, cardinality, numeric ranges, cast/crew sizes,
          genre coverage. Feeds docs/Data_Design.md.
Inputs  : env TMDB_API_KEY ; optional --years (e.g. 2018-2023), --pages, --sample.
Outputs : prints a summary and writes ../docs/profile_report.md.
Run     : TMDB_API_KEY=xxx python3 tools/profile_tmdb.py --years 2018-2023 --pages 2 --sample 150
Notes   : stdlib only (urllib) so it runs with zero install. Hits the live TMDB API — run it
          locally where you have network + a free key (themoviedb.org). Rate-limit aware (429 backoff).
Last updated: 2026-06-26
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter

BASE = "https://api.themoviedb.org/3"


def _get(path: str, **params) -> dict:
    """GET a TMDB endpoint, retrying with backoff on 429/transient errors.

    Accepts either a v3 api_key (32-char hex -> sent as ?api_key= query param) or a
    v4 Read Access Token (a JWT, "eyJ..." -> sent as an Authorization: Bearer header).
    """
    key = os.environ.get("TMDB_API_KEY")
    if not key:
        sys.exit("Set TMDB_API_KEY (free key from https://www.themoviedb.org/settings/api).")
    headers: dict[str, str] = {}
    if key.startswith("eyJ"):  # v4 bearer token (JWT) -> Authorization header
        headers["Authorization"] = f"Bearer {key}"
    else:  # v3 api_key -> query param
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
                time.sleep(2 * (attempt + 1))
                continue
            raise
        except urllib.error.URLError as e:
            last_err = e
            time.sleep(1 * (attempt + 1))
    raise RuntimeError(f"failed after retries ({last_err}): {url}")


def discover(year: int, page: int) -> dict:
    return _get("/discover/movie", primary_release_year=year, sort_by="popularity.desc", page=page)


def details(movie_id: int) -> dict:
    return _get(f"/movie/{movie_id}")


def credits(movie_id: int) -> dict:
    return _get(f"/movie/{movie_id}/credits")


def collect(years: list[int], pages: int, sample: int):
    ids: list[int] = []
    for y in years:
        for p in range(1, pages + 1):
            for m in discover(y, p).get("results", []):
                ids.append(m["id"])
    ids = ids[:sample]

    rows: list[dict] = []
    cast_sizes, crew_sizes, genres_per = [], [], []
    genres, companies = Counter(), Counter()
    for i, mid in enumerate(ids, 1):
        d, c = details(mid), credits(mid)
        rows.append(d)
        cast_sizes.append(len(c.get("cast", [])))
        crew_sizes.append(len(c.get("crew", [])))
        gl = [g["name"] for g in d.get("genres", [])]
        genres_per.append(len(gl))
        genres.update(gl)
        companies.update(co["name"] for co in d.get("production_companies", []))
        if i % 25 == 0:
            print(f"  profiled {i}/{len(ids)}")
    return rows, cast_sizes, crew_sizes, genres_per, genres, companies


def coverage(rows: list[dict], field: str, predicate) -> tuple[int, int, float]:
    n = len(rows)
    k = sum(1 for r in rows if predicate(r.get(field)))
    return k, n, (k / n if n else 0.0)


def numeric_stats(rows: list[dict], field: str):
    vals = [r.get(field) for r in rows if isinstance(r.get(field), (int, float)) and r.get(field)]
    if not vals:
        return None
    return (min(vals), max(vals), round(statistics.mean(vals), 1), round(statistics.median(vals), 1))


def main() -> int:
    ap = argparse.ArgumentParser(description="Profile a TMDB sample before modeling.")
    ap.add_argument("--years", default="2018-2023", help="inclusive range, e.g. 2018-2023")
    ap.add_argument("--pages", type=int, default=2, help="discover pages per year (20 movies/page)")
    ap.add_argument("--sample", type=int, default=150, help="max movies to fan out (details+credits)")
    a = ap.parse_args()
    lo, hi = (int(x) for x in a.years.split("-"))
    years = list(range(lo, hi + 1))

    print(f"Profiling TMDB: years {lo}-{hi}, {a.pages} page(s)/yr, sample up to {a.sample} ...")
    rows, cast_sizes, crew_sizes, genres_per, genres, companies = collect(years, a.pages, a.sample)
    if not rows:
        sys.exit("No rows returned — check the key and parameters.")

    out: list[str] = ["# TMDB profiling report", "",
                      f"Sample: **{len(rows)}** movies, release years {lo}-{hi}.", ""]

    out.append("## Measure coverage (model only what's reliably present)")
    for field, pred, label in [
        ("budget", lambda v: bool(v) and v > 0, "budget > 0"),
        ("revenue", lambda v: bool(v) and v > 0, "revenue > 0"),
        ("runtime", lambda v: bool(v), "runtime present"),
        ("vote_count", lambda v: bool(v) and v > 0, "vote_count > 0"),
        ("popularity", lambda v: bool(v), "popularity present"),
        ("overview", lambda v: bool(v), "overview present"),
    ]:
        k, n, rate = coverage(rows, field, pred)
        out.append(f"- **{label}**: {k}/{n} = {rate:.0%}")
    out.append("")

    out.append("## Numeric ranges (min / max / mean / median)")
    for field in ("budget", "revenue", "runtime", "vote_average", "vote_count", "popularity"):
        s = numeric_stats(rows, field)
        out.append(f"- `{field}`: {s}" if s else f"- `{field}`: (no numeric values)")
    out.append("")

    out.append("## Cardinality & fan-out sizing")
    out.append(f"- distinct genres: {len(genres)}; avg genres/movie: {round(statistics.mean(genres_per), 2)}")
    out.append(f"- distinct production companies (sample): {len(companies)}")
    out.append(f"- cast size — min {min(cast_sizes)}, median {int(statistics.median(cast_sizes))}, "
               f"max {max(cast_sizes)} → confirms a top-N cap (default 10)")
    out.append(f"- crew size — min {min(crew_sizes)}, median {int(statistics.median(crew_sizes))}, "
               f"max {max(crew_sizes)} → extract director(s) only")
    out.append("")

    out.append("## Top genres / companies (sample)")
    out.append("- genres: " + ", ".join(f"{g} ({c})" for g, c in genres.most_common(10)))
    out.append("- companies: " + ", ".join(f"{g} ({c})" for g, c in companies.most_common(10)))

    report = "\n".join(out)
    docs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")
    os.makedirs(docs_dir, exist_ok=True)
    path = os.path.join(docs_dir, "profile_report.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(report + "\n")
    print("\n" + report + f"\n\nWrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
