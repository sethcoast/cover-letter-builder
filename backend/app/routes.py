from flask import Blueprint, request, jsonify
from .crew_ai import crew_write_cover_letter

bp = Blueprint('main', __name__)

@bp.route('/')
def hello():
    return "Hello, World!"

@bp.route('/generate-cover-letter', methods=['POST'])
def generate_cover_letter():
    print("PISS !")
    job_url = request.form['jobUrl']
    linkedin_url = request.form['linkedinUrl']
    resume_file = request.files['resumeFile']
    
    print(job_url)
    print(linkedin_url)
    print(resume_file)

    # Here you would include your agent definitions and processing logic
    cover_letter = crew_write_cover_letter(job_url, linkedin_url, resume_file)

    return jsonify({'coverLetter': cover_letter})

@bp.route('/check-crew-progress', methods=['POST'])
def generate_cover_letter():
    print("SHIT PISS !")
    job_url = request.form['jobUrl']
    linkedin_url = request.form['linkedinUrl']
    resume_file = request.files['resumeFile']
    
    print(job_url)
    print(linkedin_url)
    print(resume_file)

    # Here you would include your agent definitions and processing logic
    cover_letter = crew_write_cover_letter(job_url, linkedin_url, resume_file)

    return jsonify({'coverLetter': cover_letter})