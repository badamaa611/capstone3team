import os
from flask import Flask, render_template, request, redirect, url_for, session
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.config['SECRET_KEY'] = 'smart-brain-secret-key-2026'

# --- ӨГӨГДЛИЙН САН ---
if os.getenv("RENDER"):
    db_path = "/tmp/user.db"
else:
    basedir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(basedir, 'instance', 'user.db')
    os.makedirs(os.path.join(basedir, 'instance'), exist_ok=True)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    ner = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- GOOGLE SHEETS ХОЛБОЛТ ---
def get_test_data(grade, subject):
    scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets']
    # Жич: Render дээр 'service_account.json' файлыг оруулах эсвэл Env Variable ашиглах
    creds = ServiceAccountCredentials.from_json_keyfile_name('service_account.json', scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key('1RqJo5t0_iC0fr5bOEfCkNrAjBlmFuAe2BOZL6ewjA_A').sheet1
    data = sheet.get_all_records()
    return [row for row in data if str(row['grade']) == str(grade) and row['subject'] == subject]

# --- БЛУПРИНТ ---
from auth import auth as auth_blueprint
app.register_blueprint(auth_blueprint, url_prefix='/auth')

# --- МАРШРУТУУД ---
@app.route('/')
def index():
    # app.py-ийн сүүлийн мөрүүд:
    return render_template('test.html', grade=grade, subject=subject, questions=questions)
                           subjects_5=['Математик', 'Монгол хэл'], 
                           subjects_9=['Байгалийн ухаан', 'Математик'], 
                           subjects_12=['Математик', 'Англи хэл', 'Биологи'])

@app.route('/take-test/<grade>/<subject>', methods=['GET', 'POST'])
def take_test(grade, subject):
    questions = get_test_data(grade, subject)
    if request.method == 'POST':
        zow_too = 0
        for i, q in enumerate(questions):
            if request.form.get(f'q{i}') == str(q['answer']):
                zow_too += 1
        session['test_result'] = {
            'niit_asuult': len(questions),
            'zow_too': zow_too,
            'buruu_too': len(questions) - zow_too,
            'ai_recommendation': "Таны сургалтын үр дүн тооцоологдлоо."
        }
        return redirect(url_for('test_result_page'))
    return render_template('test.html', questions=questions)

@app.route('/result')
def test_result_page():
    result = session.get('test_result')
    if not result: return redirect(url_for('index'))
    return render_template('result.html')

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)