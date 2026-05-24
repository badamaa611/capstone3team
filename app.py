import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-brain-secret-key-2026'

# --- РЕНДЕР ОРЧИНД ЗОРИУЛСАН ӨГӨГДЛИЙН САНГИЙН ЗАМ ---
# Хэрэв Render дээр ажиллаж байгаа бол /tmp хавтас руу бичнэ
if os.getenv("RENDER"):
    db_path = "/tmp/user.db"
else:
    basedir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(basedir, 'instance', 'user.db')
    if not os.path.exists(os.path.join(basedir, 'instance')):
        os.makedirs(os.path.join(basedir, 'instance'))

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'

# --- USER ЗАГВАР ---
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

# --- БЛУПРИНТ БОЛОН БУСАД ИМПОРТ ---
from auth import auth as auth_blueprint
app.register_blueprint(auth_blueprint, url_prefix='/auth')

# БААЗ ҮҮСГЭХ
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)