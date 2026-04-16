from flask import Flask
from app.models.base import db
from app.core.config import Config

def create_app():
    app = Flask(__name__)
    
    app.config.from_object(Config)
    
    db.init_app(app)
    
    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)