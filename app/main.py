import os

from flask import Flask
from flasgger import Swagger
from werkzeug.exceptions import RequestEntityTooLarge
from app.models.base import db
from app.core.config import Config
from app.core.scheduler import start_daily_task_scheduler
from app.routers.auth_router import auth_bp
from app.routers.radiographs_router import radiographs_bp
from app.services.xray_service import XRayService


SWAGGER_TEMPLATE = {
    "swagger": "2.0",
    "info": {
        "title": "API Radiography Flask",
        "version": "1.0.0",
        "description": "Radiography API with JWT Bearer authentication",
    },
    "securityDefinitions": {
        "Authorization": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "Bearer <token>",
        }
    },
    "security": [
        {
            "Authorization": []
        }
    ],
}

def create_app():
    app = Flask(__name__)

    app.config.from_object(Config)

    db.init_app(app)
    Swagger(app, template=SWAGGER_TEMPLATE)
    app.register_blueprint(auth_bp)
    app.register_blueprint(radiographs_bp)

    if app.config.get("IMAGE_PRIVACY_SCHEDULER_ENABLED", True):
        app.extensions["image_privacy_scheduler"] = start_daily_task_scheduler(
            lambda: XRayService().enforce_private_images(),
            hour=23,
            minute=59,
        )

    @app.route("/")
    def index():
        return {"message": "API Radiography Flask is running"}, 200

    @app.errorhandler(RequestEntityTooLarge)
    def handle_file_too_large(_):
        return {
            "message": "File size exceeds configured maximum.",
            "max_file_size_mb": app.config.get("MAX_FILE_SIZE_MB", 5),
        }, 413

    return app

app = create_app()

if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_DEBUG", "0").lower() in ("1", "true", "yes")
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=debug_mode)