from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
from flask_session import Session
from celery import Celery
from crewai import Crew, Process, Agent, Task
from dotenv import load_dotenv
from crewai_tools import (
  ScrapeWebsiteTool,
  PDFSearchTool
)
from langchain_openai import ChatOpenAI
from watchdog.observers.polling import PollingObserver as Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent
from .config import Config
from .gcs import download_from_gcs, upload_to_gcs
from .fixed_pdf_search_tool import FixedPDFSearchTool
from copy import deepcopy
import agentops
import redis
import logging
import ssl
import sys
import os

# Environment variables
load_dotenv()
os.environ["OPENAI_MODEL_NAME"] = 'gpt-3.5-turbo'
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
os.environ["SERPER_API_KEY"] = os.getenv("SERPER_API_KEY")

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
    from .crew_ai import profiler, job_researcher, cover_letter_writer, cover_letter_reviewer, qa_agent, profile_task, research_task, cover_letter_compose_task, review_cover_letter_task, check_consistency_task#, assemble_and_kickoff_crew
    self.update_state(state='PROGRESS', meta={'status': 'Initializing Crew...'})
    
    agentops_key = os.getenv("AGENTOPS_API_KEY")
    if agentops_key is not None:
        print("Agentops key found!")
    agentops.init(agentops_key)
    
    # Make a deep copy of the agents and tasks to avoid conflicts
    # local_profiler = deepcopy(profiler)
    # local_job_researcher = deepcopy(job_researcher)
    # local_cover_letter_writer = deepcopy(cover_letter_writer)
    # local_cover_letter_reviewer = deepcopy(cover_letter_reviewer)
    # local_qa_agent = deepcopy(qa_agent)
    # local_profile_task = deepcopy(profile_task)
    # local_research_task = deepcopy(research_task)
    # local_cover_letter_compose_task = deepcopy(cover_letter_compose_task)
    # local_review_cover_letter_task = deepcopy(review_cover_letter_task)
    # local_check_consistency_task = deepcopy(check_consistency_task)
    
    # create temporary directory for storing output files from the Crew AI
    os.makedirs('data/' + session_id, exist_ok=True)
    # load resume file from GCS into local directory
    local_resume_file_path = os.path.abspath(resume_file_path)
    download_from_gcs('cover-letter-bucket', resume_file_path, local_resume_file_path)
    
    cover_letter_inputs = {
        'job_posting_url': job_url,
        'resume_path': local_resume_file_path,
        'linkedin_url': linkedin_url,
    }
    
    # reassign the path of the output files for each of the tasks
    profile_task.output_file = 'data/' + session_id + '/candidate_profile.txt'
    research_task.output_file = 'data/' + session_id + '/job_requirements.txt'
    cover_letter_compose_task.output_file = 'data/' + session_id + '/cover_letter.txt'
    review_cover_letter_task.output_file = 'data/' + session_id + '/cover_letter_review.txt'
    check_consistency_task.output_file = 'data/' + session_id + '/consistency_report.txt'
    
    # Tool definitions
    scrape_linkedin_tool = ScrapeWebsiteTool(website_url=linkedin_url)
    scrape_job_posting_tool = ScrapeWebsiteTool(website_url=job_url)
    semantic_search_resume = FixedPDFSearchTool(pdf=local_resume_file_path)
    # scrape_linkedin_tool.cache_function = lambda _args, _result: False
    # scrape_job_posting_tool.cache_function = lambda _args, _result: False
    # semantic_search_resume.cache_function = lambda _args, _result: False
    
    if os.path.exists(local_resume_file_path):
        print("File found!")
        print(local_resume_file_path)
    
    # Add tools to the tasks
    profiler.tools = [scrape_linkedin_tool, semantic_search_resume]
    job_researcher.tools = [scrape_job_posting_tool]
    cover_letter_writer.tools = [scrape_linkedin_tool, scrape_job_posting_tool, semantic_search_resume]
    cover_letter_reviewer.tools = [scrape_job_posting_tool]
    qa_agent.tools = [scrape_linkedin_tool, scrape_job_posting_tool, semantic_search_resume]
    
    # set up observer to watch for file changes
    crew_log_file = f'data/{session_id}/crew_log.txt'
    with open(crew_log_file, 'w'):
        pass # Open in write mode, will truncate the file if it already exists
    event_handler = FileChangeHandler()
    observer = Observer()
    observer.schedule(event_handler, path=crew_log_file, recursive=False)
    observer.start()
    
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
        cache=False,
        # cache=True,
        output_log_file=crew_log_file
    )
    
    # Redirect stdout to the logger
    # sys.stdout = LoggerWriter(logger, logging.INFO)
    # sys.stderr = LoggerWriter(logger, logging.ERROR)
    
    # try:
    # logger.info('Crew AI is running...')
    self.update_state(state='PROGRESS', meta={'status': 'Crew AI is running...'})
    ### this execution will take a few minutes to run
    result = cover_letter_crew.kickoff(inputs=cover_letter_inputs)
    
    # write output files to gcs bucket
    bucket_dir = 'data/' + session_id
    upload_to_gcs('cover-letter-bucket', bucket_dir + '/candidate_profile.txt', bucket_dir + '/candidate_profile.txt')
    upload_to_gcs('cover-letter-bucket', bucket_dir + '/job_requirements.txt', bucket_dir + '/job_requirements.txt')
    upload_to_gcs('cover-letter-bucket', bucket_dir + '/cover_letter.txt', bucket_dir + '/cover_letter.txt')
    upload_to_gcs('cover-letter-bucket', bucket_dir + '/cover_letter_review.txt', bucket_dir + '/cover_letter_review.txt')
    upload_to_gcs('cover-letter-bucket', bucket_dir + '/consistency_report.txt', bucket_dir + '/consistency_report.txt')
    
    # cover_letter_crew.clear_cache()
    agentops.end_session("Success")
    self.update_state(state='SUCCESS', meta={'status': 'Task completed!', 'result': result})
    return {'status': 'Task completed!', 'result': result}
    
class FileChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if isinstance(event, FileModifiedEvent):
            with open(event.src_path, 'r') as f:
                content = f.read()
                socketio.emit('log', {'data': content}, namespace='/')

if __name__ == '__main__':
    print("Running app...")
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')  # Basic config
    socketio.run(app, host='0.0.0.0', debug=True, port='8080')