from flask import Blueprint, request, jsonify
from .crew_ai import crew_write_cover_letter_task, crew_write_cover_letter
from .extensions import celery
import os

bp = Blueprint('main', __name__)

@bp.route('/')
def hello():
    return "Hello, World!"

@bp.route('/generate-cover-letter', methods=['POST'])
def generate_cover_letter():
    job_url = request.form['jobUrl']
    linkedin_url = request.form['linkedinUrl']
    resume_file = request.files['resumeFile']
    
    print(job_url)
    print(linkedin_url)
    print(resume_file)
    # todo: Actually this might not work. We might need to save it to redis or something
    # save resume file to local directory
    resume_file_path = os.path.join('data/input', resume_file.filename)
    resume_file.save(resume_file_path)

    # Here you would include your agent definitions and processing logic
    cover_letter = crew_write_cover_letter(job_url, linkedin_url, resume_file_path)

    return jsonify({'coverLetter': cover_letter})

@bp.route('/generate-cover-letter-task', methods=['POST'])
def generate_cover_letter_task():
    job_url = request.form['jobUrl']
    linkedin_url = request.form['linkedinUrl']
    resume_file = request.files['resumeFile']
    
    print(job_url)
    print(linkedin_url)
    print(resume_file)
    # todo: Actually this might not work. We might need to save it to redis or something
    # save resume file to local directory
    resume_file_path = os.path.join('data/input', resume_file.filename)
    resume_file.save(resume_file_path)

    # Here you would include your agent definitions and processing logic
    task = crew_write_cover_letter_task.apply_async(args=[job_url, linkedin_url, resume_file_path])

    return jsonify({'task_id': task.id})

@bp.route('/status/<task_id>')
def task_status(task_id):
    task = celery.AsyncResult(task_id)
    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'status': 'Pending...'
        }
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            'status': task.info.get('status', ''),
            'result': task.info.get('result', '') if task.state == 'SUCCESS' else ''
        }
    else:
        response = {
            'state': task.state,
            'status': str(task.info)  # Exception raised
        }
    return jsonify(response)
