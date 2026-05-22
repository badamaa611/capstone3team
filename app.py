from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-brain-secret-key-2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///superbrain.db'

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))

class ChatHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    prompt = db.Column(db.Text)
    response = db.Column(db.Text)

class TestResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    subject = db.Column(db.String(100))
    score = db.Column(db.Integer)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()

@app.route('/')
@login_required
def index():
    # Таны анхны загварт байсан ангиудын өгөгдөл
    grade_subjects = {'5': ['Математик', 'Монгол хэл'], '9': ['Физик', 'Англи хэл'], '12': ['Математик', 'Физик']}
    chats = ChatHistory.query.filter_by(user_id=current_user.id).all()
    results = TestResult.query.filter_by(user_id=current_user.id).all()
    
    # Эндээс та өөрийн анхны index.html-ээ дуудна
    return render_template('index.html', chats=chats, results=results, grade_subjects=grade_subjects)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and user.password == request.form['password']:
            login_user(user)
            return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run()