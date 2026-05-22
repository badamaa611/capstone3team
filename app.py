import os
import google.generativeai as genai
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, current_user
from flask_bcrypt import Bcrypt

# 1. Аппликейшн үүсгэх болон тохиргоо
app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-brain-secret-key-2026'

# Gemini API тохиргоо
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# Өгөгдлийн сангийн замыг тохируулах
basedir = os.path.abspath(os.path.dirname(__file__))
instance_path = os.path.join(basedir, 'instance')

if not os.path.exists(instance_path):
    os.makedirs(instance_path, exist_ok=True)

db_path = os.path.join(instance_path, 'user.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 2. Сангуудыг аппликейшнтэй холбох
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

# 3. Өгөгдлийн сангийн Модел
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

# 4. Blueprint-ийг импортлож бүртгэх
from auth import auth as auth_blueprint
app.register_blueprint(auth_blueprint, url_prefix='/auth')

# 🔥 ХАМГИЙН ЧУХАЛ: Өгөгдлийн сан устдаг алдааг засав (Зөвхөн файл байхгүй бол үүсгэнэ)
with app.app_context():
    if not os.path.exists(db_path):
        db.create_all()

# 5. Үндсэн хуудаснууд
@app.route('/', methods=['GET', 'POST'])
def index():
    ai_response = None
    user_prompt = None
    
    # Сурагчийн дүнгийн задаргааны үзүүлэн дата (Эдгээрийг дараа нь өгөгдлийн сантай холбож болно)
    student_stats = {
        'total_score': '84%',
        'total_tests': 12,
        'strong_topics': ['Математик (Процент, Тэгшитгэл)', 'Англи хэл (Үйл үг)'],
        'weak_topics': ['Физик (Механик хөдөлгөөн)', 'Монгол хэл (Хэлц үг)'],
        'details': [
            {'subject': 'Математик', 'score': 92, 'status': 'Сайн', 'color': 'var(--green2)'},
            {'subject': 'Англи хэл', 'score': 88, 'status': 'Сайн', 'color': 'var(--green2)'},
            {'subject': 'Физик', 'score': 65, 'status': 'Сул', 'color': 'var(--purple2)'},
            {'subject': 'Монгол хэл', 'score': 71, 'status': 'Дундаж', 'color': 'var(--blue2)'}
        ]
    }
    
    if request.method == 'POST' and 'prompt' in request.form:
        user_prompt = request.form.get('prompt')
        try:
            model = genai.GenerativeModel(model_name="models/gemini-1.5-flash-latest")
            system_instruction = (
                "Чи бол Super Brain системийн ухаалаг AI туслах багш байна. "
                "Сурагчид чамаас мэргэжил сонголт, шалгалтын сэдэв, монгол/англи хэлний дүрэм, "
                "математик/физикийн томьёо асууна. Чи хариултыг маш тодорхой, ойлгомжтой, "
                "сурагчдад урам зориг өгөхүйцээр, цэгцтэй (bullet points ашиглан) монгол хэлээр хариулна уу."
            )
            full_prompt = f"{system_instruction}\n\nАсуулт: {user_prompt}"
            response = model.generate_content(full_prompt)
            ai_response = response.text
        except Exception as e:
            try:
                model = genai.GenerativeModel("gemini-pro")
                response = model.generate_content(f"Хариултыг монголоор цэгцтэй өгнө үү. Асуулт: {user_prompt}")
                ai_response = response.text
            except Exception as inner_e:
                ai_response = f"Уучлаарай, AI системтэй холбогдоход алдаа гарлаа: {str(inner_e)}"

    return render_template('index.html', prompt=user_prompt, ai_response=ai_response, stats=student_stats)

@app.route('/tests')
def tests():
    return "<h3>Шалгалтын бэлтгэл тестүүд (Удахгүй нэмэгдэнэ)</h3><a href='/'>Нүүр хуудас руу буцах</a>"

@app.route('/ai-chat')
def ai_chat():
    return "<h3>AI Зөвлөх систем (Удахгүй нэмэгдэнэ)</h3><a href='/'>Нүүр хуудас руу буцах</a>"

if __name__ == '__main__':
    app.run(debug=True)