from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt

auth = Blueprint('auth', __name__)
bcrypt = Bcrypt()

# --- 1. БҮРТГҮҮЛЭХ ХЭСЭГ ---
@auth.route('/register', methods=['GET', 'POST'])
def register():
    # Тойрог импортоос сэргийлж функц дотор импорт хийж байна
    from app import db, User  
    
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        ner = request.form.get('ner')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', 'suragch')
        grade = request.form.get('grade')

        user_exists = User.query.filter_by(email=email).first()
        if user_exists:
            flash('Энэ цахим хаяг аль хэдийн бүртгэгдсэн байна!', 'danger')
            return redirect(url_for('auth.register'))

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        
        new_user = User(
            ner=ner, 
            email=email, 
            password=hashed_password, 
            role=role, 
            grade=grade
        )
        
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Бүртгэл амжилттай! Та одоо нэвтэрч болно.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            print(f"БҮРТГЭХЭД ГАРСАН АЛДАА: {e}")
            flash('Бүртгэх үед дотоод алдаа гарлаа.', 'danger')
            
    return render_template('register.html')


# --- 2. НЭВТРЭХ ХЭСЭГ ---
@auth.route('/login', methods=['GET', 'POST'])
def login():
    # Тойрог импортоос сэргийлж функц дотор импорт хийж байна
    from app import db, User  
    
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash('Амжилттай нэвтэрлээ!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Цахим хаяг эсвэл нууц үг буруу байна!', 'danger')
            
    return render_template('login.html')


# --- 3. СИСТЕМЭЭС ГАРАХ ХЭСЭГ ---
@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Системээс амжилттай гарлаа.', 'info')
    return redirect(url_for('index'))