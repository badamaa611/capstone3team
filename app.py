import os
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin

# 1. Аппликейшн үүсгэх болон тохиргоо
app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-brain-secret-key-2026'

# Өгөгдлийн сангийн замыг instance/user.db хавтас руу яг таг зааж өгөх
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance', 'user.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 2. Өгөгдлийн сан болон Логин менежер бэлдэх
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

# 3. Өгөгдлийн сангийн Модел (Таны HTML дээрх .ner-тэй ижил)
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    ner = db.Column(db.String(150), nullable=False)   # Хэрэв username байсан бол 'ner' болгов
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='suragch') # 'bagsh' эсвэл 'suragch'
    grade = db.Column(db.String(20), nullable=True)                  # Анги (Жишээ нь: 12А)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 4. Blueprint-ийг импортлож бүртгэх
from auth import auth as auth_blueprint
app.register_blueprint(auth_blueprint, url_prefix='/auth')

# 5. Үндсэн хуудаснуудын замууд (Routes)
@app.route('/')
def index():
    # Таны илгээсэн Tabler дүрсүүдтэй гоё шинэ нүүр хуудас
    return render_template('index.html')

@app.route('/tests')
def tests():
    return "<h3>Шалгалтын бэлтгэл тестүүд (Удахгүй нэмэгдэнэ)</h3><a href='/'>Нүүр хуудас руу буцах</a>"

@app.route('/ai-chat')
def ai_chat():
    return "<h3>AI Зөвлөх систем (Удахгүй нэмэгдэнэ)</h3><a href='/'>Нүүр хуудас руу буцах</a>"

# 6. Аппликейшнийг эхлүүлэх
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Өгөгдлийн санг зөв багануудтай шинээр үүсгэх
    app.run(debug=True)
    # app.py-ийн хамгийн доор байх ёстой код:
if __name__ == '__main__':
    with app.app_context():
        # instance хавтас байхгүй бол автоматаар үүсгэх ложик
        os.makedirs(os.path.dirname(app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')), exist_ok=True)
        db.create_all()  # Өгөгдлийн санг зөв багануудтай шинээр үүсгэх
    app.run(debug=True)