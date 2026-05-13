from flask import Flask, render_template, redirect, url_for, request
from extensions import db, bcrypt, login_manager
import os

def create_app():
    app = Flask(__name__)
    base_dir = os.path.abspath(os.path.dirname(__file__))
    app.config["SECRET_KEY"] = "capstone-secret-2025"
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        "sqlite:///" + os.path.join(base_dir, "capstone.db")
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    from api.auth_routes import auth_bp, google_bp
    from api.test_routes import test_bp
    from api.ai_routes import ai_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(google_bp, url_prefix="/login")
    app.register_blueprint(test_bp, url_prefix="/api")
    app.register_blueprint(ai_bp, url_prefix="/api/ai")

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/test")
    def test_page():
        from flask_login import current_user
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))
        angi = request.args.get("angi", "12")
        hicheel = request.args.get