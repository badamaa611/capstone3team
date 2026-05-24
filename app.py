import os
import random
import csv
import io
import requests
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-brain-secret-key-2026'
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance', 'user.db')

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'

# User загварыг энд тодорхойлно
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    ner = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='suragch')
    grade = db.Column(db.String(20), nullable=True)

# ЭНЭ ХЭСЭГ АЛГА БАЙСАН ТУЛ АЛДАА ГАРЧ БАЙСАН
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# (CSV функц болон бусад код хэвээрээ...)
from auth import auth as auth_blueprint
app.register_blueprint(auth_blueprint, url_prefix='/auth')

# Database үүсгэх
with app.app_context():
    db.create_all()

# ... бусад маршрутууд ...