from flask_socketio import SocketIO
from celery import Celery

socketio = SocketIO()
celery = Celery()

def init_socketio(app):
    socketio.init_app(app, cors_allowed_origins="*")

def init_celery(app):
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
