from flask import Flask
from flasgger import Swagger
from werkzeug.exceptions import RequestEntityTooLarge
from app.models.base import db
from app.core.config import Config
from app.routers.xray_router import xray_bp

def create_app():
    app = Flask(__name__)
    
    app.config.from_object(Config)
    
    db.init_app(app)
    Swagger(app)
    app.register_blueprint(xray_bp)

    @app.errorhandler(RequestEntityTooLarge)
    def handle_file_too_large(_):
        return {
            "message": "File size exceeds configured maximum.",
            "max_file_size_mb": app.config.get("MAX_FILE_SIZE_MB", 5),
        }, 413
    
    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)