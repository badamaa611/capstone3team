import os
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt

# Өгөгдлийн бааз болон Моделиудыг зөв импортлох
from extensions import db
from models import User, Question, TestSession, TestAnswer, WeakTopic

# API Route-үүдийг дуудаж оруулж ирэх
from api.test_routes import test_bp
from api.ai_routes import ai_bp

app = Flask(__name__)

# --- 1. АЮУЛГҮЙ БАЙДАЛ БОЛОН ОРЧНЫ ТОХИРУУЛГА ---
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "super-secret-dev-key-12345")

# Өгөгдлийн баазын холболт (PostgreSQL эсвэл SQLite)
database_url = os.getenv("DATABASE_URL")
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///capstone.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- 2. САНГУУДЫГ ХӨТӨЛБӨРТЭЙ ХОЛБОХ ---
db.init_app(app)  # extensions.py-д үүсгэсэн db-г апп-тай холбох
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = "Энэ хуудас руу хандахын тулд эхлээд нэвтэрнэ үү."
login_manager.login_message_category = "info"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- 3. BLUEPRINTS БҮРТГЭХ ---
app.register_blueprint(test_bp, url_prefix="/api")
app.register_blueprint(ai_bp, url_prefix="/api")

# --- 4. ВЭБ ХУУДАСНЫ ҮНДСЭН ROUTE-ҮҮД ---

@app.route('/')
def index():
    """Нүүр хуудас"""
    return render_template('index.html')

@app.route('/test')
@login_required
def test_page():
    """Тест бөглөх хуудас"""
    angi = request.args.get('angi', '12')
    hicheel = request.args.get('hicheel', '')
    
    if not hicheel:
        flash("Уучлаарай, хичээл сонгогдоогүй байна.", "warning")
        return redirect(url_for('index'))
        
    return render_template('test.html', angi=angi, hicheel=hicheel)

@app.route('/result')
@login_required
def result_page():
    """Шалгалтын хариу харуулах хуудас"""
    onoo = request.args.get('onoo', 0)
    niit = request.args.get('niit', 0)
    return render_template('result.html', onoo=onoo, niit=niit)


# --- 5. ХЭРЭГЛЭГЧ БҮРТГҮҮЛЭХ, НЭВТРЭХ СИСТЕМ ---

@app.route('/login', methods=['GET', 'POST'], endpoint='auth.login')
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('nuuts_ug', '')  # HTML дээрх name="nuuts_ug"

        # Хэрэглэгчийг имэйлээр нь хайх
        user = User.query.filter_by(email=email).first()
        
        # models.py дээр нууц үг нь 'nuuts_ug' багананд хадгалагдаж байгаа
        if user and bcrypt.check_password_hash(user.nuuts_ug, password):
            login_user(user)
            flash('Амжилттай нэвтэрлээ!', 'success')
            
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Имэйл эсвэл нууц үг буруу байна!', 'danger')
            
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'], endpoint='auth.register')
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        ner = request.form.get('ner', '').strip()          
        email = request.form.get('email', '').strip()      
        password = request.form.get('nuuts_ug', '')       
        duwer = request.form.get('duwer', 'suragch')       
        angi = request.form.get('angi', '').strip()        
        
        if not ner or not email or not password:
            flash('Нэр, И-мэйл, Нууц үг талбарыг заавал бөглөнө үү!', 'danger')
            return render_template('register.html')
            
        user_exists = User.query.filter_by(email=email).first()
        if user_exists:
            flash('Энэ имэйл хаяг аль хэдийн бүртгэгдсэн байна.', 'danger')
            return render_template('register.html')
            
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        
        new_user = User(
            ner=ner, 
            email=email, 
            nuuts_ug=hashed_password, 
            duwer=duwer, 
            angi=angi
        )
        
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Бүртгэл амжилттай боллоо! Одоо нэвтэрч болно.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Бүртгэхэд алдаа гарлаа: {str(e)}', 'danger')
            
    return render_template('register.html')


@app.route('/logout', endpoint='auth.logout')
@login_required
def logout():
    logout_user()
    flash('Системээс амжилттай гарлаа.', 'info')
    return redirect(url_for('auth.login'))


# --- app.py-ийн доод хэсгийг ингэж шинэчилнэ ---

with app.app_context():
    db.create_all()
    
    # Баганы хамгаалалт
    try:
        from sqlalchemy import text
        db.session.execute(text("ALTER TABLE question ADD COLUMN sedew VARCHAR(100);"))
        db.session.commit()
    except Exception:
        db.session.rollback()

    # Хэрэв бааз хоосон бол туршилтын 2 асуулт автоматаар нэмэх логик
    if Question.query.count() == 0:
        demo_q1 = Question(
            asuult_text="Монгол улсын нийслэл хот юу вэ?",
            zow_hariult="Улаанбаатар",
            buruu_hariult1="Дархан",
            buruu_hariult2="Эрдэнэт",
            buruu_hariult3="Чойбалсан",
            angi="12",
            hicheel="Газарзүй",
            sedew="Хүн амын газарзүй"
        )
        demo_q2 = Question(
            asuult_text="2-ийг үржих нь 2 тэнцүү хэд вэ?",
            zow_hariult="4",
            buruu_hariult1="2",
            buruu_hariult2="5",
            buruu_hariult3="6",
            angi="12",
            hicheel="Математик",
            sedew="Үржүүлэхийн үйлдэл"
        )
        db.session.add(demo_q1)
        db.session.add(demo_q2)
        db.session.commit()