from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-brain-2026-secure'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///superbrain.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ner = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), default='suragch')
    grade = db.Column(db.String(20))
    chats = db.relationship('ChatHistory', backref='author', lazy=True)

class ChatHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    prompt = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()

@app.route('/', methods=['GET', 'POST'])
def index():
    chats = []
    if request.method == 'POST':
        prompt = request.form.get('prompt')
        response = "Энэ бол AI-ын хариулт" 
        if current_user.is_authenticated:
            new_chat = ChatHistory(user_id=current_user.id, prompt=prompt, response=response)
            db.session.add(new_chat)
            db.session.commit()
            chats = ChatHistory.query.filter_by(user_id=current_user.id).all()
        else:
            chats = [{'prompt': prompt, 'response': response}]
    elif current_user.is_authenticated:
        chats = ChatHistory.query.filter_by(user_id=current_user.id).all()
    return render_template('index.html', chats=chats)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form.get('email')).first()
        if user and bcrypt.check_password_hash(user.password, request.form.get('password')):
            login_user(user)
            return redirect(url_for('index'))
        flash('И-мэйл эсвэл нууц үг буруу!', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        if User.query.filter_by(email=email).first():
            flash('Энэ и-мэйл бүртгэлтэй байна!', 'danger')
            return redirect(url_for('register'))
        
        hashed_pw = bcrypt.generate_password_hash(request.form.get('password')).decode('utf-8')
        new_user = User(ner=request.form.get('ner'), email=email, 
                        password=hashed_pw, role=request.form.get('role'), 
                        grade=request.form.get('grade'))
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run()