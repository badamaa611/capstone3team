from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from app import db, User  # Үндсэн app.py-аас db болон User-ийг импортлох

auth = Blueprint('auth', __name__)
bcrypt = Bcrypt()  # Нууц үгийг хадгалах, шалгах функцүүдийг бэлдэх

# --- 1. БҮРТГҮҮЛЭХ ХЭСЭГ ---
@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        ner = request.form.get('ner')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', 'suragch')  # Сонгоогүй бол 'suragch' гэж хадгална
        grade = request.form.get('grade')          # Анги (Жишээ нь: 12А)

        # 1. Ийм цахим хаягтай хэрэглэгч өмнө нь бүртгүүлсэн эсэхийг шалгах
        user_exists = User.query.filter_by(email=email).first()
        if user_exists:
            flash('Энэ цахим хаяг аль хэдийн бүртгэгдсэн байна!', 'danger')
            return redirect(url_for('auth.register'))

        # 2. Нууц үгийг Bcrypt-ээр кодлох (Энэ нь нэвтрэх үеийн шалгалттай яг таарна)
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        
        # 3. Шинэ хэрэглэгчийг үүсгэх
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
            flash('Бүртгэх үед дотоод алдаа гарлаа. Терминалаа шалгана уу.', 'danger')
            
    return render_template('register.html')


# --- 2. НЭВТРЭХ ХЭСЭГ ---
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # 1. Хэрэглэгчийг имэйл хаягаар нь өгөгдлийн сангаас хайх
        user = User.query.filter_by(email=email).first()
        
        # 2. Хэрэглэгч олдсон бөгөөд нууц үг нь Bcrypt кодлолтой таарч байвал
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash('Амжилттай нэвтэрлээ!', 'success')
            return redirect(url_for('index'))  # Үндсэн нүүр хуудас руу шилжинэ
        else:
            print("НЭВТРЭХЭД ГАРСАН АЛДАА: Имэйл эсвэл нууц үг зөрүүтэй байна.")
            flash('Цахим хаяг эсвэл нууц үг буруу байна!', 'danger')
            
    return render_template('login.html')


# --- 3. СИСТЕМЭЭС ГАРАХ ХЭСЭГ ---
@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Системээс амжилттай гарлаа.', 'info')
    return redirect(url_for('index'))