import logging
from datetime import datetime
from typing import Any
from urllib.parse import urlparse

from flask import Blueprint, jsonify, request
from sqlalchemy import asc, desc, func, or_
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import BadRequest

from database import db
from models.movie import Movie

logger = logging.getLogger(__name__)

movie_bp = Blueprint("movies", __name__)

DEFAULT_PAGE = 1
DEFAULT_PER_PAGE = 12
MAX_PER_PAGE = 100
VALID_SORT_FIELDS = {"title", "rating", "release_year", "created_at"}
DEFAULT_SORT_BY = "created_at"
DEFAULT_SORT_ORDER = "desc"


def build_response(
    success: bool,
    message: str = "",
    data: Any = None,
    errors: list[str] | None = None,
    status_code: int = 200,
    **extra,
):
    payload: dict[str, Any] = {"success": success, "message": message}

    if data is not None:
        payload["data"] = data

    if errors is not None:
        payload["errors"] = errors

    payload.update(extra)
    return jsonify(payload), status_code


def get_json_payload() -> dict:
    if not request.is_json:
        raise BadRequest("Request body must be JSON")

    payload = request.get_json(silent=True)
    if payload is None:
        raise BadRequest("Malformed JSON body")

    if not isinstance(payload, dict):
        raise BadRequest("JSON payload must be an object")

    return payload


def is_valid_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def parse_int_field(value: Any, field_name: str, min_value: int | None = None, max_value: int | None = None) -> tuple[int | None, str | None]:
    if value is None:
        return None, f"{field_name} is required"

    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None, f"{field_name} must be an integer"

    if min_value is not None and parsed < min_value:
        return None, f"{field_name} must be at least {min_value}"

    if max_value is not None and parsed > max_value:
        return None, f"{field_name} must be at most {max_value}"

    return parsed, None


def parse_float_field(value: Any, field_name: str, min_value: float | None = None, max_value: float | None = None) -> tuple[float | None, str | None]:
    if value is None:
        return None, f"{field_name} is required"

    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None, f"{field_name} must be a number"

    if min_value is not None and parsed < min_value:
        return None, f"{field_name} must be at least {min_value}"

    if max_value is not None and parsed > max_value:
        return None, f"{field_name} must be at most {max_value}"

    return parsed, None


def validate_movie_payload(payload: dict) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    cleaned: dict[str, Any] = {}
    current_year = datetime.utcnow().year

    title = payload.get("title")
    if not isinstance(title, str) or not title.strip():
        errors.append("title is required and cannot be empty")
    else:
        title = title.strip()
        if len(title) > 255:
            errors.append("title must be 255 characters or fewer")
        else:
            cleaned["title"] = title

    genre = payload.get("genre")
    if not isinstance(genre, str) or not genre.strip():
        errors.append("genre is required and cannot be empty")
    else:
        genre = genre.strip()
        if len(genre) > 100:
            errors.append("genre must be 100 characters or fewer")
        else:
            cleaned["genre"] = genre

    release_year, error = parse_int_field(payload.get("release_year"), "release_year", 1888, current_year + 1)
    if error:
        errors.append(error)
    else:
        cleaned["release_year"] = release_year

    duration, error = parse_int_field(payload.get("duration"), "duration", 1)
    if error:
        errors.append(error)
    else:
        cleaned["duration"] = duration

    rating, error = parse_float_field(payload.get("rating"), "rating", 0.0, 10.0)
    if error:
        errors.append(error)
    else:
        cleaned["rating"] = rating

    status = payload.get("status")
    if not isinstance(status, str) or not status.strip():
        errors.append("status is required and cannot be empty")
    else:
        status = status.strip()
        if status not in Movie.STATUSES:
            errors.append(f"status must be one of: {', '.join(Movie.STATUSES)}")
        else:
            cleaned["status"] = status

    description = payload.get("description")
    if description is None:
        cleaned["description"] = None
    elif not isinstance(description, str):
        errors.append("description must be a string")
    else:
        description = description.strip()
        if len(description) > 2000:
            errors.append("description must be 2000 characters or fewer")
        else:
            cleaned["description"] = description

    poster_url = payload.get("poster_url")
    if poster_url is None:
        cleaned["poster_url"] = None
    elif not isinstance(poster_url, str):
        errors.append("poster_url must be a string")
    else:
        poster_url = poster_url.strip()
        if poster_url and not is_valid_url(poster_url):
            errors.append("poster_url must be a valid http or https URL")
        elif len(poster_url) > 500:
            errors.append("poster_url must be 500 characters or fewer")
        else:
            cleaned["poster_url"] = poster_url or None

    return cleaned, errors


def get_sort_clause(sort_by: str, sort_order: str) -> tuple[Any, str | None]:
    if sort_by not in VALID_SORT_FIELDS:
        return desc(Movie.created_at), f"sort_by must be one of: {', '.join(sorted(VALID_SORT_FIELDS))}"

    order = sort_order.lower()
    if order not in {"asc", "desc"}:
        return desc(Movie.created_at), "sort_order must be 'asc' or 'desc'"

    column = getattr(Movie, sort_by)
    return asc(column) if order == "asc" else desc(column), None


def parse_pagination_params() -> tuple[int, int, list[str]]:
    errors: list[str] = []
    page, error = parse_int_field(request.args.get("page", DEFAULT_PAGE), "page", 1)
    if error:
        errors.append(error)

    per_page, error = parse_int_field(request.args.get("per_page", DEFAULT_PER_PAGE), "per_page", 1, MAX_PER_PAGE)
    if error:
        errors.append(error)

    return page or DEFAULT_PAGE, per_page or DEFAULT_PER_PAGE, errors


def parse_query_filters(query_params: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    filters: dict[str, Any] = {}

    query_text = query_params.get("q")
    if isinstance(query_text, str) and query_text.strip():
        filters["q"] = query_text.strip()
    elif query_text is not None and str(query_text).strip() == "":
        errors.append("q cannot be empty")

    genre = query_params.get("genre")
    if isinstance(genre, str) and genre.strip():
        filters["genre"] = genre.strip()
    elif genre is not None and str(genre).strip() == "":
        errors.append("genre cannot be empty")

    status = query_params.get("status")
    if status is not None:
        if not isinstance(status, str) or not status.strip():
            errors.append("status must be a non-empty string")
        else:
            status = status.strip()
            if status not in Movie.STATUSES:
                errors.append(f"status must be one of: {', '.join(Movie.STATUSES)}")
            else:
                filters["status"] = status

    rating = query_params.get("rating")
    if rating is not None and str(rating).strip() != "":
        parsed_rating, rating_error = parse_float_field(rating, "rating", 0.0, 10.0)
        if rating_error:
            errors.append(rating_error)
        else:
            filters["rating"] = parsed_rating

    release_year = query_params.get("release_year")
    if release_year is not None and str(release_year).strip() != "":
        parsed_year, year_error = parse_int_field(
            release_year,
            "release_year",
            1888,
            datetime.utcnow().year + 1,
        )
        if year_error:
            errors.append(year_error)
        else:
            filters["release_year"] = parsed_year

    return filters, errors


def build_movie_query(filters: dict[str, Any]) -> Any:
    query = Movie.query

    if filters.get("q"):
        search_term = f"%{filters['q']}%"
        query = query.filter(
            or_(
                Movie.title.ilike(search_term),
                Movie.genre.ilike(search_term),
                Movie.description.ilike(search_term),
            )
        )

    if filters.get("genre"):
        query = query.filter(Movie.genre.ilike(f"%{filters['genre']}%"))

    if filters.get("status"):
        query = query.filter(Movie.status == filters["status"])

    if filters.get("rating") is not None:
        query = query.filter(Movie.rating >= filters["rating"])

    if filters.get("release_year") is not None:
        query = query.filter(Movie.release_year == filters["release_year"])

    return query


def paginate_query(query: Any, sort_clause: Any, page: int, per_page: int) -> Any:
    return query.order_by(sort_clause).paginate(page=page, per_page=per_page, error_out=False)


def execute_query_endpoint(
    query_params: dict[str, Any],
    success_message: str,
    require_search: bool = False,
    require_filter: bool = False,
) -> tuple[Any, int]:
    filters, errors = parse_query_filters(query_params)
    if require_search and not filters.get("q"):
        errors.append("Query parameter 'q' is required")

    if require_filter and not any(
        filters.get(field) is not None
        for field in ("q", "genre", "status", "rating", "release_year")
    ):
        errors.append(
            "At least one filter parameter is required: genre, status, rating, release_year, or q"
        )

    sort_by = query_params.get("sort_by", DEFAULT_SORT_BY)
    sort_order = query_params.get("sort_order", DEFAULT_SORT_ORDER)
    sort_clause, sort_error = get_sort_clause(sort_by, sort_order)
    if sort_error:
        errors.append(sort_error)

    page, per_page, pagination_errors = parse_pagination_params()
    errors.extend(pagination_errors)

    if errors:
        return build_response(False, message="Invalid query parameters", errors=errors, status_code=400)

    query = build_movie_query(filters)
    pagination = paginate_query(query, sort_clause, page, per_page)

    return build_response(
        True,
        message=success_message,
        data=[movie.to_dict() for movie in pagination.items],
        page=page,
        per_page=per_page,
        total=pagination.total,
        pages=pagination.pages,
    )


@movie_bp.route("/movies", methods=["GET"])
def list_movies():
    return execute_query_endpoint(request.args, success_message="Movies retrieved")


@movie_bp.route("/movies/<int:movie_id>", methods=["GET"])
def get_movie(movie_id: int):
    movie = db.session.get(Movie, movie_id)
    if movie is None:
        return build_response(False, message="Movie not found", status_code=404)

    return build_response(True, message="Movie retrieved", data=movie.to_dict())


@movie_bp.route("/movies", methods=["POST"])
def create_movie():
    payload = get_json_payload()
    cleaned, errors = validate_movie_payload(payload)
    if errors:
        return build_response(False, message="Validation failed", errors=errors, status_code=400)

    movie = Movie(**cleaned)
    db.session.add(movie)

    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Database failure while creating movie")
        return build_response(False, message="Failed to create movie", status_code=500)

    return build_response(True, message="Movie created", data=movie.to_dict(), status_code=201)


@movie_bp.route("/movies/<int:movie_id>", methods=["PUT"])
def update_movie(movie_id: int):
    payload = get_json_payload()
    movie = db.session.get(Movie, movie_id)
    if movie is None:
        return build_response(False, message="Movie not found", status_code=404)

    cleaned, errors = validate_movie_payload(payload)
    if errors:
        return build_response(False, message="Validation failed", errors=errors, status_code=400)

    for key, value in cleaned.items():
        setattr(movie, key, value)

    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Database failure while updating movie")
        return build_response(False, message="Failed to update movie", status_code=500)

    return build_response(True, message="Movie updated", data=movie.to_dict())


@movie_bp.route("/movies/<int:movie_id>", methods=["DELETE"])
def delete_movie(movie_id: int):
    movie = db.session.get(Movie, movie_id)
    if movie is None:
        return build_response(False, message="Movie not found", status_code=404)

    db.session.delete(movie)

    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Database failure while deleting movie")
        return build_response(False, message="Failed to delete movie", status_code=500)

    return build_response(True, message="Movie deleted")


@movie_bp.route("/movies/search", methods=["GET"])
def search_movies():
    return execute_query_endpoint(
        request.args,
        success_message="Search results retrieved",
        require_search=True,
    )


@movie_bp.route("/movies/filter", methods=["GET"])
def filter_movies():
    return execute_query_endpoint(
        request.args,
        success_message="Filter results retrieved",
        require_filter=True,
    )


@movie_bp.route("/health", methods=["GET"])
def get_health():
    return build_response(True, message="Service healthy", status="healthy")


@movie_bp.route("/dashboard", methods=["GET"])
def get_dashboard():
    totals = db.session.query(Movie.status, func.count(Movie.id)).group_by(Movie.status).all()
    status_counts = {status: count for status, count in totals}
    average_rating = db.session.query(func.avg(Movie.rating)).scalar() or 0.0

    return build_response(
        True,
        message="Dashboard summary retrieved",
        data={
            "total_movies": db.session.query(func.count(Movie.id)).scalar() or 0,
            "watching": status_counts.get("Watching", 0),
            "completed": status_counts.get("Completed", 0),
            "plan_to_watch": status_counts.get("Plan to Watch", 0),
            "dropped": status_counts.get("Dropped", 0),
            "average_rating": round(float(average_rating), 2),
        },
    )


@movie_bp.route("/genres", methods=["GET"])
def get_genres():
    results = db.session.query(Movie.genre).distinct().order_by(Movie.genre).all()
    genres = [row[0] for row in results]

    return build_response(True, message="Genres retrieved", data=genres)
