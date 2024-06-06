from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
from celery import Celery
from app.config import Config
from app.crew_ai import cover_letter_crew
from app.logger import setup_logger
import logging
import sys
# import eventlet

# eventlet.monkey_patch()

# Initialize the Flask app
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:5173"}})

app.config['SECRET_KEY'] = 'secret!'
app.config['CELERY_BROKER_URL'] = Config.CELERY_BROKER_URL
app.config['CELERY_RESULT_BACKEND'] = Config.CELERY_RESULT_BACKEND
app.config.from_object("app.config.Config")

from app.routes import bp
app.register_blueprint(bp)

# Initialize the SocketIO app
socketio = SocketIO(app, cors_allowed_origins="http://localhost:5173", message_queue=Config.SOCKET_IO_MESSAGE_QUEUE, async_mode='threading')

# setup logger
logger = setup_logger(socketio)

# Initialize the Celery app
def make_celery(app):
    celery = Celery(
        app.import_name,
        broker=app.config['CELERY_BROKER_URL'],
        backend=app.config['CELERY_RESULT_BACKEND']
    )
    celery.conf.update(app.config)
    return celery
celery = make_celery(app)

@celery.task(bind=True)
def crew_write_cover_letter_task(self, job_url, linkedin_url, resume_file_path):
    cover_letter_inputs = {
        'job_posting_url': job_url,
        'resume_path': resume_file_path,
        'linkedin_url': linkedin_url,
    }
    
    # Redirect stdout to the logger
    sys.stdout = LoggerWriter(logger, logging.INFO)
    sys.stderr = LoggerWriter(logger, logging.ERROR)
    
    try:
        logger.info('Crew AI is running...')
        self.update_state(state='PROGRESS', meta={'status': 'Crew AI is running...'})
        
        ### this execution will take a few minutes to run
        result = cover_letter_crew.kickoff(inputs=cover_letter_inputs)
        self.update_state(state='SUCCESS', meta={'status': 'Task completed!', 'result': result})
        return {'status': 'Task completed!', 'result': result}
    except Exception as e:
        self.update_state(state='FAILURE', meta={'status': 'Task failed!', 'error': str(e)})
        logger.error(f'Task failed: {str(e)}')
        raise e
    finally:
        # Reset stdout and stderr
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

class LoggerWriter:
    def __init__(self, logger, level):
        self.logger = logger
        self.level = level

    def write(self, message):
        if message.strip() != "":
            self.logger.log(self.level, message)

    def flush(self):
        pass

if __name__ == '__main__':
    print("Running app...")
    socketio.run(app, debug=True, port='5001')