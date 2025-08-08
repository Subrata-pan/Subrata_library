from flask import Flask, render_template, request
import os
from werkzeug.utils import secure_filename
from models import db, Ebook

app = Flask(__name__)

# Upload folder setup
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# SQLite DB setup
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Home route
@app.route('/')
def home():
    return render_template('index.html')

# Upload route
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file = request.files['ebook']
        title = request.form.get('title')
        author = request.form.get('author')
        category = request.form.get('category')

        if file and file.filename.endswith('.pdf'):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # Save ebook info to database
            new_ebook = Ebook(title=title, file_path=filepath, author=author, category=category)
            db.session.add(new_ebook)
            db.session.commit()

            return f"✅ '{title}' uploaded and saved to database!"
        else:
            return "❌ Only PDF files are allowed."
    return render_template('upload.html')

# Initialize DB (Run this once)
@app.before_first_request
def create_tables():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
