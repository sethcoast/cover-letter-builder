from flask import Blueprint, request, jsonify
import os
import uuid

bp = Blueprint('main', __name__)

@bp.route('/')
def hello():
    return "Hello, World!"

@bp.route('/generate-cover-letter', methods=['POST'])
def generate_cover_letter():
    from .crew_ai import crew_write_cover_letter
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
    from app.app import crew_write_cover_letter_task
    job_id = str(uuid.uuid4())
    job_url = request.form['jobUrl']
    linkedin_url = request.form['linkedinUrl']
    resume_file = request.files['resumeFile']
    
    print(job_url)
    print(linkedin_url)
    print(resume_file)
    # todo: Actually this might not work. We might need to save it to redis or something
    # save resume file to local directory
    os.mkdir('data/' + job_id)
    os.mkdir('data/' + job_id + '/input')
    os.mkdir('data/' + job_id + '/output')
    resume_file_path = os.path.join('data/' + job_id + '/input', resume_file.filename)
    print('resume file path: ', resume_file_path)
    resume_file.save(resume_file_path)

    # Here you would include your agent definitions and processing logic
    task = crew_write_cover_letter_task.apply_async(args=[job_url, linkedin_url, resume_file_path, job_id])

    return jsonify({'task_id': task.id})

@bp.route('/status/<task_id>')
def task_status(task_id):
    from .app import celery
    print("Status endpoint hit! Task ID: ", task_id)
    task = celery.AsyncResult(task_id)
    try:
        print("Task state: ", task.state)
    except Exception as e:
        print("Task state error: ", str(e))
        return jsonify({'status': 'Task not found!'})
        
    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'status': 'Pending...'
        }
    elif task.state == 'REVOKED':
        response = {
            'state': task.state,
            'status': 'Task cancelled!'
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
        print("FAILURE:", response)
    return jsonify(response)

@bp.route('/cancel-task/<task_id>', methods=['POST'])
def cancel_task(task_id):
    from .app import celery
    print("Cancel endpoint hit! Task ID: ", task_id)
    celery.control.revoke(task_id, terminate=True, signal='SIGKILL')
    
    return jsonify({'status': 'Task cancelled!'})
