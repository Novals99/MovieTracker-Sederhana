import logging

from flask import Flask, jsonify
from flask_cors import CORS
from werkzeug.exceptions import BadRequest, HTTPException

from config import Config
from database import db
from routes.movie import movie_bp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app, origins=Config.CORS_ORIGINS)

    db.init_app(app)
    app.register_blueprint(movie_bp)
    register_error_handlers(app)

    logger.info("MovieTracker API initialized")
    return app


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(BadRequest)
    def handle_bad_request(error):
        return jsonify(success=False, message="Malformed JSON or invalid request"), 400

    @app.errorhandler(404)
    def handle_not_found(error):
        return jsonify(success=False, message="Resource not found"), 404

    @app.errorhandler(405)
    def handle_method_not_allowed(error):
        return jsonify(success=False, message="Method not allowed"), 405

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        if isinstance(error, HTTPException):
            logger.warning("HTTP exception: %s", error)
            return jsonify(success=False, message=error.description), error.code

        logger.exception("Unexpected error")
        return jsonify(success=False, message="Internal server error"), 500


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
