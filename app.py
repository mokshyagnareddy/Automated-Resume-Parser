from flask import Flask, render_template, request
import os
from werkzeug.utils import secure_filename
from resume_parser import parse_resume # type: ignore

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def index():
    parsed_data = None
    error = None

    if request.method == 'POST':
        if 'resume' not in request.files:
            error = 'No file uploaded'
        else:
            file = request.files['resume']
            if file.filename.endswith('.pdf'):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)

                try:
                    parsed_data = parse_resume(file_path)
                except Exception as e:
                    error = f"Error parsing resume: {str(e)}"
            else:
                error = 'Only PDF files are supported'

    return render_template('index.html', parsed_data=parsed_data, error=error)

if __name__ == '__main__':
    app.run(debug=True)
