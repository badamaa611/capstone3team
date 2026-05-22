import os
import random
import requests
import csv
import google.genai as genai
import re  # Холбоосноос ID-г автоматаар таслах сан
from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

# 1. СИСТЕМИЙН ҮНДСЭН ТОХИРГОО
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'super-brain-secret-key-12345')

# Render дээрх PostgreSQL холболт, эсвэл локал SQLite бааз хамгаалалт
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///super_brain.db')
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# ⚠️ УХААЛАГ ХАМГААЛАЛТ: Бүтэн URL эсвэл зөвхөн ID аль нь ч байсан автоматаар цэвэрлэж авна
RAW_SHEET_INPUT = os.getenv('GOOGLE_SHEET_ID', '1RqJo5t0_iC0fr5bOEfCkNrAjBlmFuAe2BOZL6ewjA_A')

if "docs.google.com/spreadsheets" in RAW_SHEET_INPUT:
    match = re.search(r'/d/([^/]+)', RAW_SHEET_INPUT)
    GOOGLE_SHEET_ID = match.group(1) if match else RAW_SHEET_INPUT
else:
    GOOGLE_SHEET_ID = RAW_SHEET_INPUT

# 2. ӨГӨГДЛИЙН БААЗЫН МОДЕЛУУД
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ner = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    angi = db.Column(db.String(10), nullable=False)        # 5, 9, 12
    hicheel = db.Column(db.String(100), nullable=False)    # Математик, Физик...
    sedew = db.Column(db.String(150), nullable=True)       # Сэдэв
    asuult_text = db.Column(db.Text, nullable=False)       # Асуулт
    zow_hariult = db.Column(db.Text, nullable=False)       # Зөв хариулт
    buruu_hariult1 = db.Column(db.Text, nullable=False)    # Буруу 1
    buruu_hariult2 = db.Column(db.Text, nullable=False)    # Буруу 2
    buruu_hariult3 = db.Column(db.Text, nullable=False)    # Буруу 3

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 3. ХЭРЭГЛЭГЧИЙН СИСТЕМ
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Системд амжилттай нэвтэрлээ!', 'success')
            return redirect(url_for('index'))
        flash('Имэйл эсвэл нууц үг буруу байна!', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        ner = request.form.get('ner', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        if User.query.filter_by(email=email).first():
            flash('Энэ имэйл хаяг аль хэдийн бүртгэгдсэн байна!', 'danger')
            return redirect(url_for('register'))
            
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(ner=ner, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        
        login_user(new_user)
        flash('Бүртгэл амжилттай үүсэж, нэвтэрлээ!', 'success')
        return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Системээс гарлаа.', 'info')
    return redirect(url_for('index'))

# 4. ҮНДСЭН ХУУДАС
@app.route('/')
def index():
    subjects = []
    try:
        distinct_subs = db.session.query(Question.angi, Question.hicheel).distinct().all()
        subjects = [{"angi": s[0], "hicheel": s[1]} for s in distinct_subs]
    except Exception:
        subjects = []
    return render_template('index.html', subjects=subjects)

# 5. ТЕСТҮҮДИЙН ЛОГИК
@app.route('/get-questions', methods=['GET'])
@login_required
def get_questions():
    angi = request.args.get('angi', '').strip()
    hicheel = request.args.get('hicheel', '').strip()
    questions = []
    
    try:
        if angi and hicheel:
            questions = Question.query.filter(
                (Question.angi == str(angi)) & 
                (Question.hicheel.ilike(f"%{hicheel}%"))
            ).limit(10).all()
        if not questions and angi:
            questions = Question.query.filter_by(angi=str(angi)).limit(10).all()
        if not questions:
            questions = Question.query.limit(10).all()
    except Exception as e:
        print(f"Баазаас асуулт уншихад алдаа: {e}")

    if not questions:
        return jsonify({
            "questions": [{
                "id": 999,
                "asuult": f"Уучлаарай, {angi}-р ангийн '{hicheel}' хичээлийн асуулт баазад хараахан ороогүй байна. Багш Google Sheet-ээс импорт хийх шаардлагатай.",
                "sedew": "Мэдэгдэл",
                "choices": [
                    {"text": "Ойлголоо, багшид мэдэгдэе", "is_correct": True},
                    {"text": "Хаах", "is_correct": False}
                ]
            }]
        })

    output = []
    for q in questions:
        choices = [
            {"text": q.zow_hariult, "is_correct": True},
            {"text": q.buruu_hariult1, "is_correct": False},
            {"text": q.buruu_hariult2, "is_correct": False},
            {"text": q.buruu_hariult3, "is_correct": False}
        ]
        random.shuffle(choices)
        output.append({
            "id": q.id,
            "asuult": q.asuult_text,
            "sedew": q.sedew or 'Ерөнхий сэдэв',
            "choices": choices
        })
    return jsonify({"questions": output})

@app.route('/submit-test', methods=['POST'])
@login_required
def submit_test():
    data = request.json or {}
    answers = data.get('answers', [])
    zow_too, buruu_too = 0, 0
    aldsan_sedwuwd = set()
    
    for ans in answers:
        q_id = ans.get('question_id')
        selected = ans.get('selected_text')
        if q_id == 999:
            zow_too += 1
            continue
        q = Question.query.get(q_id)
        if q:
            if str(q.zow_hariult).strip() == str(selected).strip():
                zow_too += 1
            else:
                buruu_too += 1
                if q.sedew: aldsan_sedwuwd.add(q.sedew)
        else:
            buruu_too += 1

    if aldsan_sedwuwd:
        sedew_str = ", ".join(list(aldsan_sedwuwd))
        prompt = (
            f"Чи бол Super Brain системийн ухаалаг AI багш байна. Сурагч тест өгөөд дараах сэдвүүд дээр алдсан байна: {sedew_str}.\n"
            f"Эдгээр сэдэв тус бүрээр сурагчийн мэдлэгийг бататгах зорилгоор сонгох хувилбартай (MCQ) шинээр 2 асуулт зохиож өгнө үү.\n"
            f"Асуулт бүрийн доор зөв хариултыг нь заавал тэмдэглэж, тайлбарыг Монгол хэлээр маш тодорхой харуулна уу."
        )
        try:
            client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
            response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
            ai_output = response.text
        except Exception as e:
            ai_output = f"Сурагч дараах сэдвүүд дээр алдлаа: {sedew_str}. (AI зөвлөх залгагдахад алдаа гарлаа: {e})"
    else:
        ai_output = "🎉 Төгс гүйцэтгэл! Та бүх асуултандаа 100% зөв хариуллаа. Маш сайн байна!"

    return jsonify({
        "status": "success",
        "zow_too": zow_too,
        "buruu_too": buruu_too,
        "niit_asuult": len(answers),
        "ai_recommendation": ai_output
    })

# 6. УХААЛАГ GOOGLE SHEET ИМПОРТЫН СИСТЕМ (Автомат нүүр танигч хувилбар)
@app.route('/import-now', methods=['GET'])
def import_from_sheet():
    # Тэмдэглэл: Багш аа, энд хуучин gid кодыг устгаж, үндсэн хуудаснаас шууд татдаг болгов.
    csv_url = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/export?format=csv"
    try:
        response = requests.get(csv_url)
        if response.status_code != 200:
            return jsonify({
                "status": "error",
                "message": f"Google Sheet-ээс өгөгдөл татаж чадсангүй. Сэргээх код: {response.status_code}."
            }), 400
            
        csv_data = response.content.decode('utf-8').splitlines()
        reader = csv.DictReader(csv_data)
        
        fieldnames = [f.strip().lower() for f in reader.fieldnames] if reader.fieldnames else []

        try:
            db.session.query(Question).delete()
            db.session.commit()
        except Exception as db_err:
            db.session.rollback()
            return jsonify({"status": "error", "message": f"Хуучин баазыг цэвэрлэхэд алдаа гарлаа: {str(db_err)}"}), 500

        success_count = 0
        skipped_count = 0
        
        for index, row in enumerate(reader, start=2):
            clean_row = {k.strip().lower() if k else '': v for k, v in row.items()}
            
            asuult_txt = clean_row.get('asuult_text') or clean_row.get('asuult') or clean_row.get('асуулт')
            if not asuult_txt:
                skipped_count += 1
                continue
                
            angi = clean_row.get('angi') or clean_row.get('анги') or '12'
            angi = str(angi).replace('-р анги', '').replace('анги', '').strip()
            
            hicheel = clean_row.get('hicheel') or clean_row.get('хичээл') or 'Ерөнхий хичээл'
            sedew = clean_row.get('sedew') or clean_row.get('сэдэв') or 'Ерөнхий сэдэв'
            
            zow = clean_row.get('zow_hariult') or clean_row.get('zow') or clean_row.get('зөв')
            b1 = clean_row.get('buruu_hariult1') or clean_row.get('buruu1') or clean_row.get('буруу1') or "Хувилбар 1"
            b2 = clean_row.get('buruu_hariult2') or clean_row.get('buruu2') or clean_row.get('буруу2') or "Хувилбар 2"
            b3 = clean_row.get('buruu_hariult3') or clean_row.get('buruu3') or clean_row.get('буруу3') or "Хувилбар 3"
            
            new_q = Question(
                angi=str(angi),
                hicheel=hicheel.strip(),
                sedew=sedew.strip(),
                asuult_text=asuult_txt.strip(),
                zow_hariult=zow.strip() if zow else "Зөв хариулт олдсонгүй",
                buruu_hariult1=b1.strip(),
                buruu_hariult2=b2.strip(),
                buruu_hariult3=b3.strip()
            )
            db.session.add(new_q)
            success_count += 1
            
        db.session.commit()
        return jsonify({
            "status": "success",
            "message": "SUPER BRAIN баазын асуултууд амжилттай шинэчлэгдлээ!",
            "imported_questions_count": success_count,
            "skipped_rows": skipped_count
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "error", 
            "message": "Импортын явцад дотоод алдаа (500) гарлаа.", 
            "error_details": str(e)
        }), 500

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)