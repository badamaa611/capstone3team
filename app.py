import os
import random
import csv
import io
import requests
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin
from flask_bcrypt import Bcrypt
from auth import auth as auth_blueprint

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-brain-secret-key-2026'

# --- Тохиргоо ---
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance', 'user.db')
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'

# --- CSV Унших функц (Хичээлээр шүүх) ---
SHEET_ID = '1RqJo5t0_iC0fr5bOEfCkNrAjBlmFuAe2BOZL6ewjA_A'
CSV_URL = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0'

def get_data_filtered(grade, subject=None):
    try:
        resp = requests.get(CSV_URL, timeout=10)
        resp.encoding = 'utf-8'
        reader = csv.reader(io.StringIO(resp.text))
        rows = list(reader)[1:] # Header алгасах
        
        questions = []
        for i, row in enumerate(rows):
            if len(row) < 8: continue
            # row[3]=Анги, row[4]=Хичээл
            if str(row[3]).strip() == str(grade):
                if subject and str(row[4]).strip() != str(subject):
                    continue
                
                # Сонголтуудыг холих
                correct = row[2].strip()
                options = [correct, row[5].strip(), row[6].strip(), row[7].strip()]
                random.shuffle(options)
                
                questions.append({
                    'id': i, 'q': row[0], 'image': row[1], 'subject': row[4],
                    'a': options[0], 'b': options[1], 'c': options[2], 'd': options[3],
                    'correct': chr(ord('a') + options.index(correct))
                })
        return questions
    except:
        return []

# --- Маршрутууд ---
@app.route('/', methods=['GET', 'POST'])
def index():
    # Анги бүрээр хичээлийн жагсаалт гаргах
    data = get_data_filtered(grade='all') # Энэ хэсгийг өөрийн бүтэцдээ тааруулаарай
    return render_template('index.html')

@app.route('/take-test/<grade>/<subject>', methods=['GET', 'POST'])
def take_test(grade, subject):
    questions = get_data_filtered(grade, subject)
    
    if request.method == 'POST':
        correct_count = 0
        for q in questions:
            if request.form.get(f"q_{q['id']}") == q['correct']:
                correct_count += 1
        
        score = int((correct_count / len(questions)) * 100) if questions else 0
        flash(f"{subject} хичээлийн дүн: {score}%", "success")
        return redirect(url_for('index'))

    return render_template('test.html', grade=grade, subject=subject, questions=questions)

app.register_blueprint(auth_blueprint, url_prefix='/auth')

if __name__ == '__main__':
    app.run(debug=True)