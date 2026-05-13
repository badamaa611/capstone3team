import os
from flask_dance.contrib.google import make_google_blueprint, google
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db, bcrypt
from models import User

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    if request.method == "POST":
        email    = request.form.get("email")
        nuuts_ug = request.form.get("nuuts_ug")
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.nuuts_ug, nuuts_ug):
            login_user(user)
            flash("Амжилттай нэвтэрлээ!", "success")
            return redirect(url_for("index"))
        flash("Имэйл эсвэл нууц үг буруу байна.", "error")
    return render_template("login.html")

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        ner      = request.form.get("ner")
        email    = request.form.get("email")
        nuuts_ug = request.form.get("nuuts_ug")
        duwer    = request.form.get("duwer", "suragch")
        angi     = request.form.get("angi", "")
        if User.query.filter_by(email=email).first():
            flash("Энэ имэйл бүртгэлтэй байна.", "error")
            return redirect(url_for("auth.register"))
        hash_ug = bcrypt.generate_password_hash(nuuts_ug).decode("utf-8")
        user = User(ner=ner, email=email, nuuts_ug=hash_ug, duwer=duwer, angi=angi)
        db.session.add(user)
        db.session.commit()
        flash("Бүртгэл амжилттай! Нэвтэрнэ үү.", "success")
        return redirect(url_for("auth.login"))
    return render_template("register.html")

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))
google_bp = make_google_blueprint(
    client_id=os.environ.get("GOOGLE_CLIENT_ID"),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
    scope=["profile", "email"]
)

@auth_bp.route("/google-login")
def google_login():
    if not google.authorized:
        return redirect(url_for("google.login"))
    resp = google.get("/oauth2/v2/userinfo")
    email = resp.json()["email"]
    ner = resp.json()["name"]
    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(ner=ner, email=email, nuuts_ug="google", duwer="suragch", angi="")
        db.session.add(user)
        db.session.commit()
    login_user(user)
    return redirect(url_for("index"))