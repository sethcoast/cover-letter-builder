from celery import Celery
from flask import Flask

def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
    celery.conf.update(app.config)
    return celery

app = Flask(__name__)
app.config.from_object('app.config.Config')
celery = make_celery(app)

# Import tasks to ensure they are registered with Celery
with app.app_context():
    from . import crew_ai