from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
from flask_session import Session
from celery import Celery
from crewai import Crew, Process
from crewai_tools import (
  ScrapeWebsiteTool,
  PDFSearchTool
)
from langchain_openai import ChatOpenAI
from .config import Config
from .crew_ai import profiler, job_researcher, cover_letter_writer, cover_letter_reviewer, qa_agent, profile_task, research_task, cover_letter_compose_task, review_cover_letter_task, check_consistency_task#, assemble_and_kickoff_crew
from .logger import setup_logger
from .gcs import download_from_gcs, upload_to_gcs
import redis
import logging
import ssl
import sys
import os

# Initialize the Flask app
app = Flask(__name__)
origins = [
    "http://localhost:5173",
    "https://cover-letter-builder-delta.vercel.app",
    "https://*.vercel.app"
]
CORS(app, resources={r"/*": {"origins": origins}})
app.config.from_object(Config)

# Configure session to use Redis
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_REDIS'] = redis.from_url(os.getenv('REDIS_URL'))
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
Session(app)

from .routes import bp
app.register_blueprint(bp)

# Initialize the SocketIO app
socketio = SocketIO(app,
                    cors_allowed_origins=["http://localhost:5173","https://cover-letter-builder-delta.vercel.app"],
                    message_queue=os.getenv('REDIS_URL'),
                    async_mode='threading')

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
def crew_write_cover_letter_task(self, job_url, linkedin_url, resume_file_path, session_id):
    self.update_state(state='PROGRESS', meta={'status': 'Crew AI is running...'})
    cover_letter_inputs = {
        'job_posting_url': job_url,
        'resume_path': resume_file_path,
        'linkedin_url': linkedin_url,
    }
    
    # create temporary directory for storing output files from the Crew AI
    os.makedirs('data/' + session_id, exist_ok=True)
    # load resume file from GCS into local directory
    download_from_gcs('cover-letter-bucket', resume_file_path, resume_file_path)
    
    
    # reassign the path of the output files for each of the tasks
    profile_task.output_file = 'data/' + session_id + '/candidate_profile.txt'
    research_task.output_file = 'data/' + session_id + '/job_requirements.txt'
    cover_letter_compose_task.output_file = 'data/' + session_id + '/cover_letter.txt'
    review_cover_letter_task.output_file = 'data/' + session_id + '/cover_letter_review.txt'
    check_consistency_task.output_file = 'data/' + session_id + '/consistency_report.txt'
    
    # Tool definitions
    scrape_linkedin_tool = ScrapeWebsiteTool(website_url=linkedin_url)
    scrape_job_posting_tool = ScrapeWebsiteTool(website_url=job_url)
    semantic_search_resume = PDFSearchTool(pdf=resume_file_path)
    
    # Add tools to the tasks
    profiler.tools = [scrape_linkedin_tool, semantic_search_resume]
    job_researcher.tools = [scrape_job_posting_tool]
    cover_letter_writer.tools = [scrape_linkedin_tool, scrape_job_posting_tool, semantic_search_resume]
    cover_letter_reviewer.tools = [scrape_job_posting_tool]
    qa_agent.tools = [scrape_linkedin_tool, scrape_job_posting_tool, semantic_search_resume]
    
    # Assemble the Crew
    cover_letter_crew = Crew(
        agents=[
                profiler,
                job_researcher,
                cover_letter_writer,
                cover_letter_reviewer,
                qa_agent
                ],
        tasks=[
                profile_task,
                research_task,
                cover_letter_compose_task,
                review_cover_letter_task,
                check_consistency_task
            ],
        manager_llm=ChatOpenAI(model="gpt-3.5-turbo", 
                               temperature=0.7),
        process=Process.hierarchical,
        # process=Process.sequential,
        verbose=True,
        memory=False,
        cache=True,
        output_log_file='data/' + session_id + '/crew_log.txt'
    )
    
    # Redirect stdout to the logger
    sys.stdout = LoggerWriter(logger, logging.INFO)
    sys.stderr = LoggerWriter(logger, logging.ERROR)
    
    try:
        logger.info('Crew AI is running...')
        
        ### this execution will take a few minutes to run
        result = cover_letter_crew.kickoff(inputs=cover_letter_inputs)
        
        # write output files to gcs bucket
        bucket_dir = 'data/' + session_id
        upload_to_gcs('cover-letter-bucket', bucket_dir + '/candidate_profile.txt', bucket_dir + '/candidate_profile.txt')
        upload_to_gcs('cover-letter-bucket', bucket_dir + '/job_requirements.txt', bucket_dir + '/job_requirements.txt')
        upload_to_gcs('cover-letter-bucket', bucket_dir + '/cover_letter.txt', bucket_dir + '/cover_letter.txt')
        upload_to_gcs('cover-letter-bucket', bucket_dir + '/cover_letter_review.txt', bucket_dir + '/cover_letter_review.txt')
        upload_to_gcs('cover-letter-bucket', bucket_dir + '/consistency_report.txt', bucket_dir + '/consistency_report.txt')
        
        self.update_state(state='SUCCESS', meta={'status': 'Task completed!', 'result': result})
        return {'status': 'Task completed!', 'result': result}
    except Exception as e:
        logger.error(f'Task failed: {str(e)}')
        self.update_state(state='FAILURE', meta={'exc_type': type(e).__name__, 'exc_message': str(e)})
        raise e
    finally:
        # Reset stdout and stderr
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

# Custom class to redirect stdout and stderr to the logger
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
    socketio.run(app, host='0.0.0.0', debug=True, port='8080')