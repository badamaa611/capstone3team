import os
import pandas as pd
import requests
from io import StringIO
from flask import Flask, Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_dance.contrib.google import make_google_blueprint, google

app = Flask(__name__)

# СЕРВЕРИЙН НУУЦЛАЛЫН ТОХИРГООНУУД
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "super-secret-key-12345")
# Санамж: Render-ийн Environment Variables хэсэгт DATABASE_URL-аа оруулсан байх ёстой
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///users.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# ӨГӨГДЛИЙН САН БОЛОН ЛОГИН СҮЛЖЭЭГ ХОЛБОХ ХЭСЭГ
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "google.login"

# ӨГӨГДЛИЙН САНГИЙН МОДЕЛ
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ner = db.Column(db.String(100))
    email = db.Column(db.String(120), unique=True, nullable=False)
    nuuts_ug = db.Column(db.String(100))
    duwer = db.Column(db.String(20)) # suragch, bagsh

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# GOOGLE AUTH BLUEPRINT ТОХИРГОО
google_bp = make_google_blueprint(
    client_id=os.environ.get("GOOGLE_CLIENT_ID", "ЧИНИЙ_GOOGLE_CLIENT_ID"),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET", "ЧИНИЙ_GOOGLE_CLIENT_SECRET"),
    scope=["profile", "email"]
)
app.register_blueprint(google_bp, url_prefix="/login")

# MAIN BLUEPRINT ҮҮСГЭХ (GOOGLE SHEET УНШИХ ЛОГИК)
main = Blueprint('main', __name__)
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1HkJZUebgNFtYghS55KUKcCjNVx7A4O2huEvyv1d331o/export?format=csv&gid=830552134"

def convert_imgbb_url(url):
    """
    ImgBB вэб хуудасны линкийг уншаад Flask-ийн <img> тагт 
    шууд уншигдах жинхэнэ зургийн файл руу хөрвүүлнэ.
    """
    if url is None or pd.isna(url) or str(url).strip() == "" or str(url).strip().lower() == "nan":
        return None
    
    url = str(url).strip()
    # Хэрэв ibb.co орсон боловч шууд зургийн cdn биш байвал хөрвүүлнэ
    if "ibb.co" in url and "i.ibb.co" not in url:
        parts = url.rstrip('/').split('/')
        img_id = parts[-1]
        return f"https://i.ibb.co/{img_id}/image.png"
        
    return url

@app.route("/google-login")
def google_login():
    if not google.authorized:
        return redirect(url_for("google.login"))
    try:
        resp = google.get("/oauth2/v2/userinfo")
        if not resp.ok:
            return "Google-ээс мэдээлэл авахад алдаа гарлаа.", 500
            
        info = resp.json()
        email = info["email"]
        ner = info.get("name", "Хэрэглэгч")
        
        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(ner=ner, email=email, nuuts_ug="google-auth", duwer="suragch")
            db.session.add(user)
            db.session.commit()
            
        login_user(user)
        return redirect(url_for("main.index"))
    except Exception as e:
        return f"Системд нэвтрэх явцад алдаа гарлаа: {e}", 500

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.index"))

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/dashboard')
@login_required
def dashboard():
    angi = request.args.get('angi')
    hicheel = request.args.get('hicheel')
    
    if not angi or not hicheel:
        flash("Анги болон хичээл сонгогдоогүй байна!")
        return redirect(url_for('main.index'))
        
    try:
        response = requests.get(SHEET_CSV_URL)
        response.encoding = 'utf-8'
        
        df = pd.read_csv(StringIO(response.text))
        df.columns = [c.strip() for c in df.columns]
        
        # Анги болон хичээлээр нарийн шүүлт хийх хэсэг
        filtered_df = df[
            (df['Анги'].astype(str).str.strip() == str(angi).strip()) & 
            (df['Хичээл'].astype(str).str.strip().str.lower() == str(hicheel).strip().str.lower())
        ]
        
        questions = []
        for idx, row in filtered_df.iterrows():
            raw_img = row.get('Зураг', None)
            final_img = convert_imgbb_url(raw_img) # ImgBB хөрвүүлэгч

            questions.append({
                'id': idx,
                'question_text': row.get('Асуулт', ''),
                'image_url': final_img,
                'opt_a': row.get('А', ''),
                'opt_b': row.get('Б', ''),
                'opt_c': row.get('В', ''),
                'opt_d': row.get('Г', ''),
                'correct': str(row.get('Зөв хариулт', '')).strip().upper()
            })
            
        return render_template('quiz.html', questions=questions, angi=angi, hicheel=hicheel)
        
    except Exception as e:
        print(f"Алдаа гарлаа: {e}")
        return f"Google Sheet-ээс өгөгдөл уншихад алдаа гарлаа: {str(e)}", 500

# BLUEPRINT-ИЙГ ҮНДҮҮДЭД БҮРТГЭХ СҮҮЛЧИЙН АЛХАМ
app.register_blueprint(main)

if __name__ == "__main__":
    with app.app_context():
        db.create_all() # Хэрэглэгчийн хүснэгтийг автоматаар үүсгэнэ
    app.run(debug=True)