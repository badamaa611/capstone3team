import os
import pandas as pd
import requests
from io import StringIO
from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_dance.contrib.google import make_google_blueprint, google

app = Flask(__name__)

# СЕРВЕРИЙН НУУЦЛАЛЫН ТОХИРГООНУУД
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "super-secret-key-12345")

# SUPABASE-ИЙН TENANT IDENTIFIER БОЛОН URI АЛДААГ ЗАСАХ ЛОГИК
raw_db_url = os.environ.get("DATABASE_URL", "sqlite:///users.db")
if raw_db_url.startswith("postgres://"):
    raw_db_url = raw_db_url.replace("postgres://", "postgresql://", 1)

# Хэрэв Supabase Session pooler-ийн линк орж ирвэл SQLAlchemy-д зориулж бэлдэнэ
app.config["SQLALCHEMY_DATABASE_URI"] = raw_db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "google.login"

# ӨГӨГДЛИЙН САНГИЙН МОДЕЛ
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ner = db.Column(db.String(100))
    email = db.Column(db.String(120), unique=True, nullable=False)
    nuuts_ug = db.Column(db.String(100))
    duwer = db.Column(db.String(20), default="suragch")

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# GOOGLE AUTH BLUEPRINT
google_bp = make_google_blueprint(
    client_id=os.environ.get("GOOGLE_CLIENT_ID", "ЧИНИЙ_GOOGLE_CLIENT_ID"),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET", "ЧИНИЙ_GOOGLE_CLIENT_SECRET"),
    scope=["profile", "email"],
    redirect_to="google_callback"
)
app.register_blueprint(google_bp, url_prefix="/login")

# Google-ээр амжилттай нэвтэрсний дараа дуудагдах функц
@app.route("/google-callback")
def google_callback():
    if not google.authorized:
        return redirect(url_for("google.login"))
        
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
    return redirect(url_for("index"))

@app.route("/google-login")
def google_login():
    return redirect(url_for("google.login"))

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

# GOOGLE SHEET УНШИХ ТОХИРГОО
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1HkJZUebgNFtYghS55KUKcCjNVx7A4O2huEvyv1d331o/export?format=csv&gid=830552134"

def convert_imgbb_url(url):
    if url is None or pd.isna(url) or str(url).strip() == "" or str(url).strip().lower() == "nan":
        return None
    url = str(url).strip()
    if "ibb.co" in url and "i.ibb.co" not in url:
        parts = url.rstrip('/').split('/')
        img_id = parts[-1]
        return f"https://i.ibb.co/{img_id}/image.png"
    return url

@app.route('/')
def index():
    return render_template('index.html')

# 404 АЛДААНААС СЭРГИЙЛЖ DASHBOARD ЧИГЛҮҮЛЭЛТИЙГ ҮНДҮҮД ДЭЭР ОРУУЛАВ
@app.route('/dashboard')
@login_required
def dashboard():
    angi = request.args.get('angi')
    hicheel = request.args.get('hicheel')
    
    if not angi or not hicheel:
        flash("Анги болон хичээл сонгогдоогүй байна!")
        return redirect(url_for('index'))
        
    try:
        response = requests.get(SHEET_CSV_URL)
        response.encoding = 'utf-8'
        
        df = pd.read_csv(StringIO(response.text))
        df.columns = [c.strip() for c in df.columns]
        
        # Анги, Хичээлийн өгөгдлийг цэвэрлэж шүүх
        filtered_df = df[
            (df['Анги'].astype(str).str.strip() == str(angi).strip()) & 
            (df['Хичээл'].astype(str).str.strip().str.lower() == str(hicheel).strip().str.lower())
        ]
        
        questions = []
        for idx, row in filtered_df.iterrows():
            questions.append({
                'id': idx,
                'question_text': row.get('Асуулт', ''),
                'image_url': convert_imgbb_url(row.get('Зураг', None)),
                'opt_a': row.get('А', ''),
                'opt_b': row.get('Б', ''),
                'opt_c': row.get('В', ''),
                'opt_d': row.get('Г', ''),
                'correct': str(row.get('Зөв хариулт', '')).strip().upper()
            })
            
        # Түр зуур тест харах зорилгоор quiz.html байхгүй бол JSON хэлбэрээр харуулна
        try:
            return render_template('quiz.html', questions=questions, angi=angi, hicheel=hicheel)
        except Exception:
            return jsonify({"status": "Амжилттай холбогдлоо", "angi": angi, "hicheel": hicheel, "data": questions})
        
    except Exception as e:
        return f"Google Sheet уншихад алдаа гарлаа: {str(e)}", 500

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)