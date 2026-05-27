import os
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.config['SECRET_KEY'] = 'smart-brain-secret-key-2026'

# --- ӨГӨГДЛИЙН САНГИЙН ТОХИРГОО ---
if os.getenv("RENDER"):
    db_path = "/tmp/user.db"
else:
    basedir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(basedir, 'instance', 'user.db')
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'

# --- МАРШРУТУУД ---
@app.route('/')
def index():
    return render_template('index.html', 
                           subjects_5=['Математик', 'Монгол хэл'], 
                           subjects_9=['Байгалийн ухаан', 'Математик'], 
                           subjects_12=['Математик', 'Англи хэл', 'Биологи'])

@app.route('/take-test/<grade>/<subject>', methods=['GET', 'POST'])
def take_test(grade, subject):
    if request.method == 'POST':
        # Тест шалгах логик (Энд үр дүнг session-д хадгална)
        session['test_result'] = {
            'niit_asuult': 5,
            'zow_too': 4,
            'buruu_too': 1,
            'ai_recommendation': f"{subject} сэдвээр бататгах зөвлөмж..."
        }
        return redirect(url_for('test_result_page'))
    
    return render_template('test.html', grade=grade, subject=subject)

@app.route('/result')
def test_result_page():
    result = session.get('test_result')
    if not result:
        return redirect(url_for('index'))
    return render_template('result.html')

# --- БААЗ ҮҮСГЭХ ---
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)