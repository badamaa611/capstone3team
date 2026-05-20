import os
from flask import Flask, render_template, redirect, url_for
from flask_dance.contrib.google import make_google_blueprint, google
from flask_login import login_user, current_user
from extensions import db, bcrypt, login_manager
from models import User, TestSession, Question
from google_sheets_api import import_sheet_questions
from api.auth_routes import auth_bp
from api.test_routes import test_bp
from api.ai_routes import ai_bp


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "super-secret-key-12345")

    raw_db_url = os.environ.get("DATABASE_URL", "sqlite:///users.db")
    if raw_db_url.startswith("postgres://"):
        raw_db_url = raw_db_url.replace("postgres://", "postgresql://", 1)

    app.config["SQLALCHEMY_DATABASE_URI"] = raw_db_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    app.register_blueprint(auth_bp)
    app.register_blueprint(test_bp, url_prefix="/api")
    app.register_blueprint(ai_bp, url_prefix="/api")

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    google_bp = make_google_blueprint(
        client_id=os.environ.get("GOOGLE_CLIENT_ID", ""),
        client_secret=os.environ.get("GOOGLE_CLIENT_SECRET", ""),
        scope=["profile", "email"],
        redirect_to="google_callback"
    )
    app.register_blueprint(google_bp, url_prefix="/login")

    @app.route("/google-callback")
    def google_callback():
        if not google.authorized:
            return redirect(url_for("google.login"))
        resp = google.get("/oauth2/v2/userinfo")
        if not resp.ok:
            return "Google-ээс мэдээлэл авахад алдаа гарлаа.", 500
        info = resp.json()
        email = info.get("email")
        ner = info.get("name", "Хэрэглэгч")
        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(ner=ner, email=email, nuuts_ug="google-auth", duwer="suragch")
            db.session.add(user)
            db.session.commit()
        login_user(user)
        return redirect(url_for("index"))

    @app.route("/logout")
    def logout():
        from flask_login import logout_user
        logout_user()
        return redirect(url_for("index"))

    @app.route("/")
    def index():
        if Question.query.count() == 0:
            try:
                import_sheet_questions()
            except Exception:
                pass

        progress_stats = []
        if current_user.is_authenticated:
            sessions = TestSession.query.filter_by(suragch_id=current_user.id).all()
            stats = {}
            for s in sessions:
                if not s.too:
                    continue
                pct = round((s.niit_onoo or 0) / s.too * 100)
                subject = s.hicheel or "Тодорхойгүй"
                stats.setdefault(subject, []).append(pct)
            for subject, values in stats.items():
                avg_pct = round(sum(values) / len(values))
                progress_stats.append({
                    "hicheel": subject,
                    "avg": avg_pct,
                    "tests": len(values)
                })
            progress_stats.sort(key=lambda x: x["avg"], reverse=True)

        subjects = [
            {"angi": row[0], "hicheel": row[1]}
            for row in Question.query.with_entities(Question.angi, Question.hicheel)
                .distinct().order_by(Question.angi, Question.hicheel).all()
        ]
        return render_template("index.html", progress_stats=progress_stats, subjects=subjects)

    @app.route("/test")
    def test_page():
        from flask import request
        angi = request.args.get("angi", "12")
        hicheel = request.args.get("hicheel", "Биологи")
        return render_template("test.html", angi=angi, hicheel=hicheel)

    @app.route("/result")
    def result_page():
        from flask import request
        onoo = request.args.get("onoo", "0")
        return render_template("result.html", onoo=onoo)

    return app


app = create_app()

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
