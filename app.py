import os
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

from auth import auth as auth_blueprint
app.register_blueprint(auth_blueprint, url_prefix='/auth')

with app.app_context():
    if not os.path.exists(db_path):
        db.create_all()

# Стандарт тестийн өгөгдөл
MOCK_TESTS = {
    '5': [
        {'id': 1, 'q': 'Хоёр тооны нийлбэр 45, харьцаа нь 2:3 бол их тоог ол.', 'a': '27', 'b': '18', 'c': '25', 'd': '30', 'correct': 'a', 'topic': 'Математик (Харьцаа)'},
        {'id': 2, 'q': 'Өгүүлбэрийг зөв залгалаар холбоно уу: "Би ном ... уншив."', 'a': 'ыг', 'b': 'ийг', 'c': 'ы', 'd': 'ийн', 'correct': 'b', 'topic': 'Монгол хэл (Тийн ялгал)'}
    ],
    '9': [
        {'id': 1, 'q': 'x² - 5x + 6 = 0 тэгшитгэлийн шийдүүдийг ол.', 'a': '2 ба 3', 'b': '-2 ба -3', 'c': '1 ba 6', 'd': '0 ба 5', 'correct': 'a', 'topic': 'Математик (Тэгшитгэл)'},
        {'id': 2, 'q': 'Нэгэн жигд хөдөлгөөний хурд v = 10 м/с, хугацаа t = 5 с бол явсан замыг ол.', 'a': '2 м', 'b': '50 м', 'c': '15 м', 'd': '0.5 м', 'correct': 'b', 'topic': 'Физик (Механик хөдөлгөөн)'}
    ],
    '12': [
        {'id': 1, 'q': 'f(x) = x³ - 3x функцийн уламжлалыг ол.', 'a': '3x² - 3', 'b': 'x² - 3', 'c': '3x²', 'd': '3x - 3', 'correct': 'a', 'topic': 'Математик (Уламжлал)'},
        {'id': 2, 'q': 'Which sentence is in Present Perfect tense?', 'a': 'I am eating.', 'b': 'I ate yesterday.', 'c': 'I have eaten.', 'd': 'I will eat.', 'correct': 'c', 'topic': 'Англи хэл (Үйл үг)'}
    ]
}

@app.route('/', methods=['GET', 'POST'])
def index():
    if 'student_stats' not in session:
        session['student_stats'] = {
            'total_score': 'Хүлээгдэж буй',
            'total_tests': 0,
            'strong_topics': ['Одоогоор тест ажиллаагүй байна'],
            'weak_topics': ['Одоогоор тест ажиллаагүй байна'],
            'details': [
                {'subject': 'Математик', 'score': 0, 'status': 'Идэвхгүй', 'color': 'var(--text3)'},
                {'subject': 'Англи хэл', 'score': 0, 'status': 'Идэвхгүй', 'color': 'var(--text3)'},
                {'subject': 'Физик', 'score': 0, 'status': 'Идэвхгүй', 'color': 'var(--text3)'},
                {'subject': 'Монгол хэл', 'score': 0, 'status': 'Идэвхгүй', 'color': 'var(--text3)'}
            ]
        }

    if 'chat_history' not in session:
        session['chat_history'] = []

    if request.method == 'POST' and 'prompt' in request.form:
        user_prompt = request.form.get('prompt')
        ai_response = ""
        
        try:
            model = genai.GenerativeModel("models/gemini-1.5-flash")
            system_instruction = "Чи бол Super Brain системийн ухаалаг AI туслах байна. Хариултыг маш тодорхой, цэгцтэй монгол хэлээр хариулна уу."
            context = system_instruction + "\n\n"
            for chat in session.get('chat_history', []):
                context += f"Сурагч: {chat['user']}\nХариулт: {chat['ai']}\n"
            context += f"\nШинэ асуулт: {user_prompt}"
            response = model.generate_content(context)
            ai_response = response.text
        except Exception:
            try:
                model = genai.GenerativeModel("gemini-1.5-flash")
                response = model.generate_content(user_prompt)
                ai_response = response.text
            except Exception as inner_e:
                ai_response = f"Уучлаарай, AI системтэй холбогдоход алдаа гарлаа: {str(inner_e)}"
        
        history = session.get('chat_history', [])
        history.append({'user': user_prompt, 'ai': ai_response})
        session['chat_history'] = history
        session.modified = True

    # Хамгийн сүүлийн тестийн нарийвчилсан хариуг хуудас руу дамжуулна
    detailed_results = session.get('last_test_results', None)
    return render_template('index.html', chat_history=session['chat_history'], stats=session['student_stats'], detailed_results=detailed_results)

@app.route('/take-test/<grade>', methods=['GET', 'POST'])
def take_test(grade):
    questions = MOCK_TESTS.get(grade, [])
    
    if request.method == 'POST':
        correct_count = 0
        strong = []
        weak = []
        test_report = [] # Сонгосон хариултуудыг цуглуулах жагсаалт
        
        for q in questions:
            user_ans = request.form.get(f"q_{q['id']}")
            is_correct = (user_ans == q['correct'])
            
            if is_correct:
                correct_count += 1
                strong.append(q['topic'])
            else:
                weak.append(q['topic'])
                
            # Асуулт бүрийн дэлгэрэнгүй тайлан
            test_report.append({
                'question': q['q'],
                'user_answer': user_ans.upper() if user_ans else 'Бөглөөгүй',
                'correct_answer': q['correct'].upper(),
                'is_correct': is_correct,
                'topic': q['topic']
            })
        
        score_pct = int((correct_count / len(questions)) * 100)
        
        # Үндсэн дүнгийн хавтанг шинэчлэх
        current_stats = {
            'total_score': f"{score_pct}%",
            'total_tests': session.get('student_stats', {}).get('total_tests', 0) + 1,
            'strong_topics': list(set(strong)) if strong else ['Байхгүй (Бататгах шаардлагатай)'],
            'weak_topics': list(set(weak)) if weak else ['Байхгүй (Маш сайн)'],
            'details': [
                {'subject': 'Математик', 'score': score_pct, 'status': 'Сайн' if score_pct >= 80 else 'Анхаарах', 'color': 'var(--green2)' if score_pct >= 80 else 'var(--purple2)'},
                {'subject': 'Ерөнхий эрдэм', 'score': score_pct, 'status': 'Дуусгасан', 'color': 'var(--blue2)'}
            ]
        }
        
        session['student_stats'] = current_stats
        session['last_test_results'] = {
            'grade': grade,
            'score': score_pct,
            'report': test_report
        }
        session.modified = True
        
        flash(f"{grade}-р ангийн тестийг бөглөж дууслаа.", "success")
        return redirect(url_for('index'))

    return render_template('test.html', grade=grade, questions=questions)

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