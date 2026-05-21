import os
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt

# Манай зассан API Route-үүдийг дуудаж оруулж ирэх
from api.test_routes import test_bp
from api.ai_routes import ai_bp

app = Flask(__name__)

# --- 1. АЮУЛГҮЙ БАЙДАЛ БОЛОН ОРЧНЫ ТОХИРУУЛГА ---
# Render дээр эсвэл локал дээр ажиллах нууц түлхүүр
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "super-secret-dev-key-12345")

# Өгөгдлийн баазын холболт (PostgreSQL эсвэл хөгжүүлэлтийн SQLite)
database_url = os.getenv("DATABASE_URL")
if database_url and database_url.startswith("postgres://"):
    # SQLAlchemy-ийн шинэ хувилбар 'postgresql://' форматыг шаарддаг тул засна
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///capstone.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- 2. САНГУУДЫГ ХӨТӨЛБӨРТЭЙ ХОЛБОХ ---
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'  # Хэрэв нэвтрээгүй бол энэ хаяг руу шилжүүлнэ
login_manager.login_message = "Энэ хуудас руу хандахын тулд эхлээд нэвтэрнэ үү."
login_manager.login_message_category = "info"

# --- 3. ХЭРЭГЛЭГЧИЙН МОДЕЛ (DATABASE MODEL) ---
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- 4. BLUEPRINTS БҮРТГЭХ (ХАМГИЙН ЧУХАЛ ХЭСЭГ) ---
# Бидний зассан /api/questions болон /api/generate-adaptive-question хаягууд энд бүртгэгдэнэ
app.register_blueprint(test_bp, url_prefix="/api")
app.register_blueprint(ai_bp, url_prefix="/api")

# --- 5. ВЭБ ХУУДАСНЫ ҮНДСЭН ROUTE-ҮҮД (HTML PAGES) ---

@app.route('/')
def index():
    """Нүүр хуудас: Хичээл болон анги сонгох хэсэг"""
    return render_template('index.html')

@app.route('/test')
@login_required
def test_page():
    """Тест бөглөх хуудас (test.html-ийг ачаална)"""
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

# --- 6. ХЭРЭГЛЭГЧ БҮРТГҮҮЛЭХ, НЭВТРЭХ СИСТЕМ ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Имэйл эсвэл нууц үг буруу байна!', 'danger')
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        # Хэрэглэгч бүртгэлтэй байгаа эсэхийг шалгах
        user_exists = User.query.filter((User.email == email) | (User.username == username)).first()
        if user_exists:
            flash('Энэ имэйл эсвэл хэрэглэгчийн нэр аль хэдийн бүртгэгдсэн байна.', 'danger')
            return render_template('register.html')
            
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, email=email, password=hashed_password)
        
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Бүртгэл амжилттай боллоо! Одоо нэвтэрч болно.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Бүртгэхэд алдаа гарлаа: {str(e)}', 'danger')
            
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Системээс амжилттай гарлаа.', 'success')
    return redirect(url_for('login'))

# --- 7. СЕРВЕРИЙГ АСААХ БОЛОН БААЗ ҮҮСГЭХ ---
if __name__ == '__main__':
    # Програм асах үед баазын хүснэгтүүд байхгүй бол автоматаар үүсгэнэ
    with app.app_context():
        db.create_all()
        
    # Порт тохируулга (Render-ийн шаардлагаар 0.0.0.0 порт дээр асна)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_DEBUG", "False") == "True")