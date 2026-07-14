"""
fix_posters.py — MovieTracker Poster URL Repair Utility
=========================================================
Scans every movie in the database and repairs poster_url fields that are
empty, NULL, or broken (return non-200 HTTP responses).

Valid poster URLs are left completely untouched.

Usage (run from the backend/ directory):
    python fix_posters.py

Prerequisites:
    Add your free TMDB API key to backend/.env:
        TMDB_API_KEY=your_key_here

    Get a free key at: https://www.themoviedb.org/settings/api
"""

import os
import sys
import time
import logging

import requests
from dotenv import load_dotenv

from app import create_app
from database import db
from models.movie import Movie

# ── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

load_dotenv()

TMDB_API_KEY: str = os.getenv("TMDB_API_KEY", "")
TMDB_SEARCH_URL: str = "https://api.themoviedb.org/3/search/movie"
TMDB_IMAGE_BASE: str = "https://image.tmdb.org/t/p/w500"

# Seconds to wait between TMDB requests (free tier: 40 req/10 s)
REQUEST_DELAY: float = 0.30

# Timeout for HTTP requests (connect, read)
HTTP_TIMEOUT: tuple = (5, 10)

# How many TMDB candidates to try before giving up on a movie
MAX_CANDIDATES: int = 5


# ── TMDB helpers ─────────────────────────────────────────────────────────────

def _tmdb_search(title: str, year: int) -> list[dict]:
    """
    Call the TMDB search/movie endpoint and return a list of result dicts.
    Handles HTTP errors and rate limiting gracefully.

    Args:
        title: Movie title to search for.
        year:  Release year used as a soft hint (query param).

    Returns:
        List of TMDB result dicts (may be empty on failure).
    """
    if not TMDB_API_KEY:
        logger.error("TMDB_API_KEY is not set. Cannot search TMDB.")
        return []

    params = {
        "api_key": TMDB_API_KEY,
        "query": title,
        "include_adult": "false",
        "language": "en-US",
        "page": 1,
    }

    try:
        response = requests.get(
            TMDB_SEARCH_URL, params=params, timeout=HTTP_TIMEOUT
        )

        # Rate limited — back off and retry once
        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 5))
            logger.warning("TMDB rate limit hit. Waiting %ds …", retry_after)
            time.sleep(retry_after)
            response = requests.get(
                TMDB_SEARCH_URL, params=params, timeout=HTTP_TIMEOUT
            )

        response.raise_for_status()
        return response.json().get("results", [])

    except requests.exceptions.Timeout:
        logger.error("TMDB request timed out for title %r.", title)
    except requests.exceptions.ConnectionError:
        logger.error("Network error while contacting TMDB for title %r.", title)
    except requests.exceptions.HTTPError as exc:
        logger.error("TMDB HTTP error for title %r: %s", title, exc)
    except Exception as exc:  # noqa: BLE001
        logger.error("Unexpected error searching TMDB for %r: %s", title, exc)

    return []


def _rank_candidates(
    results: list[dict], release_year: int
) -> list[dict]:
    """
    Sort TMDB candidates so the best match comes first.

    Priority:
      1. Exact release-year match (descending popularity within year matches)
      2. Remaining results sorted by descending popularity

    Args:
        results:      Raw list of TMDB search result dicts.
        release_year: The movie's known release year from our database.

    Returns:
        Re-ordered list of candidate dicts.
    """
    def _release_year(result: dict) -> int:
        date = result.get("release_date", "")
        try:
            return int(date[:4])
        except (ValueError, TypeError):
            return 0

    year_matches = [
        r for r in results if _release_year(r) == release_year
    ]
    others = [
        r for r in results if _release_year(r) != release_year
    ]

    year_matches.sort(key=lambda r: r.get("popularity", 0), reverse=True)
    others.sort(key=lambda r: r.get("popularity", 0), reverse=True)

    return year_matches + others


def _build_poster_url(poster_path: str) -> str:
    """Construct the full TMDB CDN URL from a poster_path."""
    return f"{TMDB_IMAGE_BASE}{poster_path}"


def _is_url_valid(url: str) -> bool:
    """
    Perform an HTTP HEAD request to verify that a URL returns 200 OK.
    Falls back to a GET request if HEAD is not allowed.

    Args:
        url: URL to validate.

    Returns:
        True if the URL is reachable and returns 200, False otherwise.
    """
    if not url or not url.startswith("http"):
        return False

    try:
        resp = requests.head(url, timeout=HTTP_TIMEOUT, allow_redirects=True)
        if resp.status_code == 405:
            # Server doesn't allow HEAD — try GET with streaming
            resp = requests.get(
                url, timeout=HTTP_TIMEOUT, stream=True, allow_redirects=True
            )
        return resp.status_code == 200

    except requests.exceptions.Timeout:
        logger.debug("Timeout validating URL: %s", url)
    except requests.exceptions.ConnectionError:
        logger.debug("Connection error validating URL: %s", url)
    except Exception as exc:  # noqa: BLE001
        logger.debug("Error validating URL %s: %s", url, exc)

    return False


def _find_valid_poster(title: str, release_year: int) -> str | None:
    """
    Search TMDB for a movie, rank candidates, and return the first poster
    URL that validates to HTTP 200.

    Args:
        title:        Movie title.
        release_year: Movie release year for candidate ranking.

    Returns:
        A valid poster URL string, or None if none could be found.
    """
    results = _tmdb_search(title, release_year)
    if not results:
        logger.warning("No TMDB results for %r (%d).", title, release_year)
        return None

    candidates = _rank_candidates(results, release_year)[:MAX_CANDIDATES]

    for candidate in candidates:
        poster_path = candidate.get("poster_path")
        if not poster_path:
            continue  # This candidate has no poster — try next

        url = _build_poster_url(poster_path)
        time.sleep(REQUEST_DELAY)  # Respect rate limits between image checks

        if _is_url_valid(url):
            logger.info(
                "  ✓ Found valid poster for %r → %s", title, url
            )
            return url
        else:
            logger.debug(
                "  ✗ Candidate poster invalid for %r: %s", title, url
            )

    logger.warning("No valid poster found for %r (%d).", title, release_year)
    return None


# ── Core repair logic ─────────────────────────────────────────────────────────

def _needs_repair(movie: Movie) -> bool:
    """
    Determine whether a movie's poster_url should be checked/repaired.

    A URL needs repair when it is:
      - None / empty / whitespace-only
      - Not starting with 'http'

    URL that appear well-formed will be validated via HTTP later only if
    the caller opts in (batch-validate mode). This function is the first-pass
    cheap filter.

    Args:
        movie: Movie ORM instance.

    Returns:
        True if the URL is obviously broken, False otherwise.
    """
    url = movie.poster_url
    if not url or not url.strip():
        return True
    if not url.strip().startswith("http"):
        return True
    return False


def fix_posters() -> None:
    """
    Main entry point for the poster repair utility.

    Workflow per movie:
      1. If poster_url is obviously broken → fetch from TMDB.
      2. If poster_url looks well-formed   → validate via HTTP HEAD/GET.
         - If valid   → leave untouched.
         - If invalid → fetch from TMDB.
      3. Update database only when a new valid URL is found.
      4. Commit after every successful update (no all-or-nothing risk).
    """
    if not TMDB_API_KEY:
        logger.error(
            "TMDB_API_KEY is not set in your .env file.\n"
            "Add it as:  TMDB_API_KEY=your_key_here\n"
            "Get a free key at: https://www.themoviedb.org/settings/api"
        )
        sys.exit(1)

    app = create_app()

    with app.app_context():
        movies: list[Movie] = Movie.query.order_by(Movie.title).all()
        total = len(movies)

        if total == 0:
            logger.warning("No movies found in the database. Exiting.")
            return

        logger.info("Starting poster repair for %d movies …\n", total)

        # ── Counters ──────────────────────────────────────────────────────
        count_valid = 0    # Already had a valid poster; no change needed
        count_updated = 0  # Successfully repaired
        count_skipped = 0  # No valid TMDB poster found; left unchanged
        count_errors = 0   # Unexpected errors during processing

        for idx, movie in enumerate(movies, start=1):
            prefix = f"[{idx:>3}/{total}]"

            try:
                # ── Step 1: cheap structural check ────────────────────────
                if _needs_repair(movie):
                    logger.info(
                        "%s %r — URL missing/broken. Searching TMDB …",
                        prefix, movie.title,
                    )
                else:
                    # ── Step 2: HTTP validation of existing URL ────────────
                    logger.info(
                        "%s %r — Validating existing URL …",
                        prefix, movie.title,
                    )
                    time.sleep(REQUEST_DELAY)
                    if _is_url_valid(movie.poster_url):
                        logger.info(
                            "  → Already valid. Skipping.\n"
                        )
                        count_valid += 1
                        continue
                    else:
                        logger.info(
                            "  → URL returned non-200. Searching TMDB …"
                        )

                # ── Step 3: Fetch a valid poster from TMDB ─────────────────
                time.sleep(REQUEST_DELAY)
                new_url = _find_valid_poster(movie.title, movie.release_year)

                if new_url:
                    movie.poster_url = new_url
                    db.session.commit()
                    logger.info(
                        "  → Updated successfully.\n"
                    )
                    count_updated += 1
                else:
                    logger.warning(
                        "  → No valid poster found. Record left unchanged.\n"
                    )
                    count_skipped += 1

            except Exception as exc:  # noqa: BLE001
                db.session.rollback()
                logger.error(
                    "%s Unexpected error processing %r: %s\n",
                    prefix, movie.title, exc,
                )
                count_errors += 1

        # ── Final summary ─────────────────────────────────────────────────
        separator = "=" * 52
        print(f"\n{separator}")
        print(f"  Movies scanned  : {total}")
        print(f"  Already valid   : {count_valid}")
        print(f"  Updated         : {count_updated}")
        print(f"  Skipped         : {count_skipped}  (no poster found on TMDB)")
        print(f"  Errors          : {count_errors}")
        print(
            f"  Status          : "
            f"{'Finished successfully.' if count_errors == 0 else 'Finished with errors.'}"
        )
        print(f"{separator}\n")


if __name__ == "__main__":
    fix_posters()
