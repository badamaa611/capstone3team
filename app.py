import os
import csv
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

with app.app_context():
    if not os.path.exists(db_path):
        db.create_all()

# 🔥 GOOGLE SHEET-ЭЭС ТЕСТҮҮДИЙГ РЕАЛ ЦАГТ УНШИХ ФУНКЦ
def get_sheets_data():
    # Таны өгсөн Google Sheet-ийн CSV экспорт линк
    sheet_url = "https://docs.google.com/spreadsheets/d/1RqJo5t0_iC0fr5bOEfCkNrAjBlmFuAe2BOZL6ewjA_A/export?format=csv&gid=0"
    tests_db = {}
    try:
        response = requests.get(sheet_url)
        response.encoding = 'utf-8'
        lines = response.text.splitlines()
        reader = csv.DictReader(lines)
        
        for row in reader:
            # Хоосон мөрүүдээс хамгаалах
            if not row.get('Анги') or not row.get('Асуулт'):
                continue
                
            grade = str(row['Анги']).strip()
            subject = str(row['Хичээл']).strip() if row.get('Хичээл') else 'Ерөнхий'
            
            if grade not in tests_db:
                tests_db[grade] = {}
            if subject not in tests_db[grade]:
                tests_db[grade][subject] = []
                
            tests_db[grade][subject].append({
                'id': str(row.get('ID', len(tests_db[grade][subject]) + 1)),
                'q': row['Асуулт'].strip(),
                'a': row.get('А', '').strip(),
                'b': row.get('Б', '').strip(),
                'c': row.get('В', '').strip(),
                'd': row.get('Г', '').strip(),
                'correct': row['Зөв'].strip().lower() if row.get('Зөв') else 'a',
                'image': row.get('Зураг', '').strip(), # Хэрэв зураг байгаа бол URL хадгалагдана
                'topic': f"{subject} ({row.get('Сэдэв', 'Бататгал')})"
            })
        return tests_db
    except Exception as e:
        print(f"Sheet уншихад алдаа гарлаа: {e}")
        # Алдаа гарвал ажиллах backup дата
        return {
            '5': {'Математик': [{'id':'1', 'q':'Хоёр тооны нийлбэр 45, харьцаа 2:3 бол их тоо?', 'a':'27','b':'18','c':'25','d':'30','correct':'a','image':'','topic':'Харьцаа'}]}
        }

@app.route('/', methods=['GET', 'POST'])
def index():
    if 'student_stats' not in session:
        session['student_stats'] = {
            'total_score': 'Хүлээгдэж буй', 'total_tests': 0,
            'strong_topics': ['Одоогоор тест ажиллаагүй байна'], 'weak_topics': ['Одоогоор тест ажиллаагүй байна'],
            'details': [{'subject': 'Математик', 'score': 0, 'status': 'Идэвхгүй', 'color': 'var(--text3)'}]
        }
    if 'chat_history' not in session:
        session['chat_history'] = []

    if request.method == 'POST' and 'prompt' in request.form:
        user_prompt = request.form.get('prompt')
        try:
            model = genai.GenerativeModel("models/gemini-1.5-flash")
            system_instruction = "Чи бол Super Brain системийн AI туслах байна. Цэгцтэй монгол хэлээр хариулна уу."
            context = system_instruction + "\n\n" + f"Сурагч: {user_prompt}"
            response = model.generate_content(context)
            ai_response = response.text
        except Exception:
            ai_response = "AI систем түр хугацаанд завгүй байна."
            
        history = session.get('chat_history', [])
        history.append({'user': user_prompt, 'ai': ai_response})
        session['chat_history'] = history
        session.modified = True

    # Сүүлийн тестийн дэлгэрэнгүй хариуг хуудас руу илгээх
    detailed_results = session.get('last_test_results', None)
    
    # Сүлжээний өгөгдлийг уншиж, нүүр хуудасны анги бүрт ямар хичээл байгааг илгээнэ
    all_data = get_sheets_data()
    grade_subjects = {grade: list(subjects.keys()) for grade, subjects in all_data.items()}

    return render_template('index.html', chat_history=session['chat_history'], stats=session['student_stats'], detailed_results=detailed_results, grade_subjects=grade_subjects)

@app.route('/take-test/<grade>/<subject>', methods=['GET', 'POST'])
def take_test(grade, subject):
    all_data = get_sheets_data()
    questions = injustices = all_data.get(grade, {}).get(subject, [])
    
    if not questions:
        flash("Уучлаарай, энэ хичээл дээр одоогоор асуулт бэлдэгдээгүй байна.", "info")
        return redirect(url_for('index'))

    if request.method == 'POST':
        correct_count = 0
        strong, weak, test_report = [], [], []
        
        for q in questions:
            user_ans = request.form.get(f"q_{q['id']}")
            is_correct = (user_ans == q['correct'].lower() if user_ans else False)
            
            if is_correct:
                correct_count += 1
                strong.append(q['topic'])
            else:
                weak.append(q['topic'])
                
            test_report.append({
                'question': q['q'],
                'user_answer': user_ans.upper() if user_ans else 'Бөглөөгүй',
                'correct_answer': q['correct'].upper(),
                'is_correct': is_correct,
                'topic': q['topic']
            })
        
        score_pct = int((correct_count / len(questions)) * 100)
        
        current_stats = {
            'total_score': f"{score_pct}%",
            'total_tests': session.get('student_stats', {}).get('total_tests', 0) + 1,
            'strong_topics': list(set(strong)) if strong else ['Байхгүй'],
            'weak_topics': list(set(weak)) if weak else ['Байхгүй'],
            'details': [{'subject': subject, 'score': score_pct, 'status': 'Дуусгасан', 'color': 'var(--blue2)'}]
        }
        
        session['student_stats'] = current_stats
        session['last_test_results'] = {'grade': f"{grade} ({subject})", 'score': score_pct, 'report': test_report}
        session.modified = True
        return redirect(url_for('index'))

    return render_template('test.html', grade=grade, subject=subject, questions=questions)

@app.route('/clear-chat')
def clear_chat():
    session.pop('chat_history', None)
    return redirect(url_for('index'))

@app.route('/clear-results')
def clear_results():
    session.pop('last_test_results', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)