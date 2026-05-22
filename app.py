import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-brain-2026-secure'
# Render дээр өгөгдөл хадгалахын тулд sqlite ашиглав
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///superbrain_v2.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login' # Чиглүүлэх хаяг 'login'

# --- ӨГӨГДЛИЙН САНГИЙН ХҮСНЭГТҮҮД ---

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    ner = db.Column(db.String(150), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    chats = db.relationship('ChatHistory', backref='author', lazy=True)
    results = db.relationship('TestResult', backref='student', lazy=True)

class ChatHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    prompt = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)

class TestResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    grade = db.Column(db.String(20), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Хүснэгтүүдийг үүсгэх
with app.app_context():
    db.create_all()

# --- МАРШРУТУУД (ROUTES) ---

@app.route('/')
@login_required # Заавал нэвтэрсэн байх
def index():
    # Зөвхөн тухайн нэвтэрсэн хэрэглэгчийн өгөгдлийг татах
    user_chats = ChatHistory.query.filter_by(user_id=current_user.id).all()
    user_results = TestResult.query.filter_by(user_id=current_user.id).all()
    
    # Таны анхны загварт байсан ангиуд
    grade_subjects = {'5': ['Математик', 'Монгол хэл'], '9': ['Физик', 'Англи хэл'], '12': ['Математик', 'Физик']}
    
    return render_template('index.html', 
                           chats=user_chats, 
                           results=user_results, 
                           grade_subjects=grade_subjects)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and bcrypt.check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('index'))
        flash('Нэвтрэх нэр эсвэл нууц үг буруу байна.', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        hashed_pw = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
        new_user = User(username=request.form['username'], 
                        ner=request.form['ner'], 
                        password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        flash('Амжилттай бүртгүүллээ. Одоо нэвтэрнэ үү.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/take-test/<grade>/<subject>')
@login_required
def take_test(grade, subject):
    # Энд тестийн логик ажиллаад дууссаны дараа:
    # new_res = TestResult(user_id=current_user.id, subject=subject, score=85, grade=grade)
    # db.session.add(new_res)
    # db.session.commit()
    return f"Тест ажиллаж байна: {grade}-р анги, {subject}"

if __name__ == '__main__':
    app.run(debug=True)