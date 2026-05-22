import os
import google.generativeai as genai
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin
from flask_bcrypt import Bcrypt

# 1. Аппликейшн үүсгэх болон тохиргоо
app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-brain-secret-key-2026'

# Gemini API тохиргоо (Render Environment-ээс уншина)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# Өгөгдлийн сангийн замыг тохируулах
basedir = os.path.abspath(os.path.dirname(__file__))
instance_path = os.path.join(basedir, 'instance')

if not os.path.exists(instance_path):
    os.makedirs(instance_path, exist_ok=True)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(instance_path, 'user.db')
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

# Өгөгдлийн санг шалгаж, зөвхөн байхгүй бол үүсгэх
with app.app_context():
    db.create_all()

# 5. Үндсэн хуудаснууд
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/tests')
def tests():
    return "<h3>Шалгалтын бэлтгэл тестүүд (Удахгүй нэмэгдэнэ)</h3><a href='/'>Нүүр хуудас руу буцах</a>"

@app.route('/ai-chat')
def ai_chat():
    return "<h3>AI Зөвлөх систем (Удахгүй нэмэгдэнэ)</h3><a href='/'>Нүүр хуудас руу буцах</a>"

# 6. Хиймэл оюуны хайлтын зам
@app.route('/ai-search', methods=['POST'])
def ai_search():
    user_prompt = request.form.get('prompt')
    if not user_prompt:
        return redirect(url_for('index'))
        
    try:
        system_instruction = (
            "Чи бол Super Brain системийн ухаалаг AI туслах багш байна. "
            "Сурагчид чамаас мэргэжил сонголт, шалгалтын сэдэв, монгол/англи хэлний дүрэм, "
            "дотоод болон олон улсын шалгалтын удирдамж, математик/физикийн томьёо асууна. "
            "Чи хариултыг маш тодорхой, ойлгомжтой, сурагчдад урам зориг өгөхүйцээр, "
            "цэгцтэй (bullet points ашиглан) монгол хэлээр хариулна уу."
        )
        
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=system_instruction
        )
        
        response = model.generate_content(user_prompt)
        ai_response = response.text
        
    except Exception as e:
        ai_response = f"Уучлаарай, AI системтэй холбогдоход алдаа гарлаа: {str(e)}"
        
    return render_template('ai_result.html', prompt=user_prompt, response=ai_response)

if __name__ == '__main__':
    app.run(debug=True)