from flask import Flask
from flask_cors import CORS
from .extensions import socketio, init_socketio, celery, init_celery

def create_app(config_class="app.config.Config"):
    app = Flask(__name__)
    app.config.from_object(config_class)
    CORS(app)

    init_socketio(app)
    init_celery(app)

    from .routes import bp
    app.register_blueprint(bp)

    return app
