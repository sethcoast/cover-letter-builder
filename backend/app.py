from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/')
def hello():
    return "Hello, World!"

@app.route('/generate-cover-letter', methods=['POST'])
def generate_cover_letter():
    print("PISS !")
    # job_url = request.form['jobUrl']
    # linkedin_url = request.form['linkedinUrl']
    # resume_file = request.files['resumeFile']

    # Here you would include your agent definitions and processing logic
    cover_letter = "Your generated cover letter will be here."

    return jsonify({'coverLetter': cover_letter})

if __name__ == '__main__':
    app.run(debug=True, port=5001)