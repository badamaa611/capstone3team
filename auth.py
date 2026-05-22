from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash

# 'auth' нэртэй Блүпринт үүсгэх
auth = Blueprint('auth', __name__)

from app import db, User

# --- БҮРТГҮҮЛЭХ ЛОГИК ---
@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            role = request.form.get('role', 'suragch')
            grade = request.form.get('grade', '')
            
            # Шаардлагатай талбарууд хоосон эсэхийг шалгах
            if not username or not email or not password:
                flash('Шаардлагатай талбаруудыг бүрэн бөглөнө үү!', 'danger')
                return redirect(url_for('auth.register'))

            # Имэйл бүртгэлтэй эсэхийг шалгах
            user_exists = User.query.filter_by(email=email).first()
            if user_exists:
                flash('Энэ и-мэйл хаяг аль хэдийн бүртгэгдсэн байна!', 'danger')
                return redirect(url_for('auth.register'))
                
            # Нууц үгийг аюулгүйгээр хаш код болгох (хамгийн сүүлийн найдвартай арга)
            hashed_password = generate_password_hash(password)
            
            # Шинэ хэрэглэгчийг 'ner' баганад хадгалах
            new_user = User(
                ner=username, 
                email=email, 
                password=hashed_password, 
                role=role, 
                grade=grade
            )
            db.session.add(new_user)
            db.session.commit()
            
            flash('Амжилттай бүртгүүллээ! Одоо нэвтэрнэ үү.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            print(f"БҮРТГЭХЭД ГАРСАН АЛДАА: {e}")
            flash('Бүртгэх үед дотоод алдаа гарлаа. Терминалаа шалгана уу.', 'danger')
            return redirect(url_for('auth.register'))
        
    return render_template('register.html')

# --- НЭВТРЭХ ЛОГИК ---
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        try:
            email = request.form.get('email')
            password = request.form.get('password')
            
            # Өгөгдлийн сангаас имэйлээр хайх
            user = User.query.filter_by(email=email).first()
            
            # Хэрэглэгч олдоод, нууц үг нь таарч байвал нэвтрүүлнэ
            if user and check_password_hash(user.password, password):
                login_user(user)
                flash(f'Тавтай морил, {user.ner}!', 'success')
                return redirect(url_for('index'))
            else:
                flash('И-мэйл эсвэл нууц үг буруу байна!', 'danger')
                return redirect(url_for('auth.login'))
                
        except Exception as e:
            print(f"НЭВТРЭХЭД ГАРСАН АЛДАА: {e}")
            flash('Нэвтрэх үед дотоод алдаа гарлаа. Терминалаа шалгана уу.', 'danger')
            return redirect(url_for('auth.login'))
            
    return render_template('login.html')

# --- СИСТЕМЭЭС ГАРАХ ЛОГИК ---
@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Системээс амжилттай гарлаа.', 'info')
    return redirect(url_for('index'))