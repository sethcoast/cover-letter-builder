from flask import Blueprint, request, jsonify, send_file
from .crew_ai import crew_write_cover_letter
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

    # Here you would include your agent definitions and processing logic
    cover_letter = crew_write_cover_letter(job_url, linkedin_url, resume_file)

    return jsonify({'coverLetter': cover_letter})

@bp.route('/clear-logs', methods=['GET'])
def clear_logs():
    log_filename = "crew_output.log"
    log_filepath = os.path.abspath(log_filename)
    if os.path.exists(log_filepath):
        # print("Log file found")
        os.remove(log_filepath)
        return jsonify({'message': 'Log file cleared'})
    else:
        # print("Log fisasssle nota fund")
        return jsonify({'error': 'Log file not found'}), 404

@bp.route('/get-logs', methods=['GET'])
def get_logs():
    log_filename = "crew_output.log"
    log_filepath = os.path.abspath(log_filename)
    if os.path.exists(log_filepath):
        # print("Log file found")
        return send_file(log_filepath, as_attachment=True)
    else:
        # print("Log file not found")
        return jsonify({'error': 'Log file not found'}), 404