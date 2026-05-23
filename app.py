import os
import random
import csv
import io
import requests
import google.generativeai as genai
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, current_user
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-brain-secret-key-2026'

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

basedir = os.path.abspath(os.path.dirname(__file__))
instance_path = os.path.join(basedir, 'instance')
if not os.path.exists(instance_path):
    os.makedirs(instance_path, exist_ok=True)

db_path = os.path.join(instance_path, 'user.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    ner = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='suragch')
    grade = db.Column(db.String(20), nullable=True)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ============================================================
# Google Sheet CSV-ээр уншина (public sheet)
# Баганы дараалал:
# A=Асуулт, B=Зураг link, C=Зөв хариулт,
# D=Анги, E=Хичээл, F=Буруу1, G=Буруу2, H=Буруу3
# ============================================================
SHEET_ID = '1RqJo5t0_iC0fr5bOEfCkNrAjBlmFuAe2BOZL6ewjA_A'
CSV_URL = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0'

def get_sheet_data():
    try:
        resp = requests.get(CSV_URL, timeout=10)
        resp.encoding = 'utf-8'
        reader = csv.reader(io.StringIO(resp.text))
        rows = list(reader)
        return rows[1:]  # header алгасна
    except Exception as e:
        print(f"Sheet алдаа: {e}")
        return []

def get_questions_by_grade(grade):
    rows = get_sheet_data()
    questions = []
    for i, row in enumerate(rows):
        if len(row) < 4:
            continue
        row_grade = str(row[3]).strip()
        if row_grade != str(grade):
            continue

        question_text = row[0].strip() if row[0] else ''
        image_link    = row[1].strip() if len(row) > 1 else ''
        correct_ans   = row[2].strip() if len(row) > 2 else ''
        subject       = row[4].strip() if len(row) > 4 else ''
        wrong1        = row[5].strip() if len(row) > 5 else ''
        wrong2        = row[6].strip() if len(row) > 6 else ''
        wrong3        = row[7].strip() if len(row) > 7 else ''

        if not question_text or not correct_ans:
            continue

        options = [o for o in [correct_ans, wrong1, wrong2, wrong3] if o]
        random.shuffle(options)
        correct_key = chr(ord('a') + options.index(correct_ans))

        questions.append({
            'id': i + 1,
            'q': question_text,
            'image': image_link,
            'subject': subject,
            'correct': correct_key,
            'a': options[0] if len(options) > 0 else '',
            'b': options[1] if len(options) > 1 else '',
            'c': options[2] if len(options) > 2 else '',
            'd': options[3] if len(options) > 3 else '',
        })
    return questions

def get_subjects_by_grade(grade):
    rows = get_sheet_data()
    subjects = []
    for row in rows:
        if len(row) < 5:
            continue
        if str(row[3]).strip() == str(grade):
            subj = row[4].strip()
            if subj and subj not in subjects:
                subjects.append(subj)
    return subjects

# ============================================================

from auth import auth as auth_blueprint
app.register_blueprint(auth_blueprint, url_prefix='/auth')

with app.app_context():
    if not os.path.exists(db_path):
        db.create_all()

@app.route('/', methods=['GET', 'POST'])
def index():
    if 'student_stats' not in session:
        session['student_stats'] = {
            'total_score': 'Хүлээгдэж буй',
            'total_tests': 0,
            'strong_topics': ['Одоогоор тест ажиллаагүй байна'],
            'weak_topics': ['Одоогоор тест ажиллаагүй байна'],
            'details': []
        }
    if 'chat_history' not in session:
        session['chat_history'] = []

    if request.method == 'POST' and 'prompt' in request.form:
        user_prompt = request.form.get('prompt')
        try:
            model = genai.GenerativeModel(model_name="gemini-1.5-flash")
            system_instruction = (
                "Чи бол Super Brain системийн ухаалаг AI туслах байна. "
                "Хариултыг маш тодорхой, цэгцтэй монгол хэлээр хариулна уу."
            )
            context = system_instruction + "\n\n"
            for chat in session['chat_history']:
                context += f"Сурагч: {chat['user']}\nБагш: {chat['ai']}\n"
            context += f"\nШинэ асуулт: {user_prompt}"
            response = model.generate_content(context)
            ai_response = response.text
            history = session['chat_history']
            history.append({'user': user_prompt, 'ai': ai_response})
            session['chat_history'] = history
            session.modified = True
        except Exception as e:
            ai_response = f"Уучлаарай, алдаа гарлаа: {str(e)}"
            session['chat_history'].append({'user': user_prompt, 'ai': ai_response})
            session.modified = True

    subjects_5  = get_subjects_by_grade('5')
    subjects_9  = get_subjects_by_grade('9')
    subjects_12 = get_subjects_by_grade('12')

    return render_template('index.html',
        chat_history=session['chat_history'],
        stats=session['student_stats'],
        subjects_5=subjects_5,
        subjects_9=subjects_9,
        subjects_12=subjects_12
    )

@app.route('/take-test/<grade>', methods=['GET', 'POST'])
@app.route('/take-test/<grade>/', methods=['GET', 'POST'])
def take_test(grade):
    questions = get_questions_by_grade(grade)

    if request.method == 'POST':
        correct_count = 0
        strong, weak = [], []
        for q in questions:
            user_ans = request.form.get(f"q_{q['id']}")
            if user_ans == q['correct']:
                correct_count += 1
                strong.append(q.get('subject', ''))
            else:
                weak.append(q.get('subject', ''))

        score_pct = int((correct_count / len(questions)) * 100) if questions else 0
        session['student_stats'] = {
            'total_score': f"{score_pct}%",
            'total_tests': session['student_stats'].get('total_tests', 0) + 1,
            'strong_topics': list(set(strong)) if strong else ['Байхгүй'],
            'weak_topics': list(set(weak)) if weak else ['Маш сайн байна!'],
            'details': []
        }
        session.modified = True
        flash(f"{grade}-р ангийн тестийг дуусгалаа. Гүйцэтгэл: {score_pct}%", "success")
        return redirect(url_for('index'))

    return render_template('test.html', grade=grade, questions=questions)

@app.route('/clear-chat')
def clear_chat():
    session.pop('chat_history', None)
    return redirect(url_for('index'))

@app.route('/tests')
def tests():
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
