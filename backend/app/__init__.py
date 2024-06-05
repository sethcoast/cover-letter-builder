from flask import Flask
from flask_cors import CORS
from .celery_app import make_celery
from .config import Config

def create_app(config_class="app.config.Config"):
    app = Flask(__name__)
    app.config.from_object(config_class)
    CORS(app)
    
    celery = make_celery(app)

    # with app.app_context():
    from . import routes
    app.register_blueprint(routes.bp)

    return app, celery