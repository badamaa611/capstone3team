import os
from urllib.parse import urlparse, urlencode, urlunparse, parse_qsl
from flask import Flask, render_template, redirect, url_for
from flask_dance.contrib.google import make_google_blueprint, google
from flask_login import login_user, current_user
from sqlalchemy.exc import OperationalError as SAOperationalError
from extensions import db, bcrypt, login_manager
from models import User, TestSession, Question
from google_sheets_api import import_sheet_questions
from api.auth_routes import auth_bp
from api.test_routes import test_bp
from api.ai_routes import ai_bp


def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "super-secret-key-12345")

    raw_db_url = os.environ.get("DATABASE_URL", "sqlite:///users.db")
    if raw_db_url.startswith("postgres://"):
        raw_db_url = raw_db_url.replace("postgres://", "postgresql://", 1)

    if raw_db_url.startswith("postgresql://") and "sslmode=" not in raw_db_url:
        parsed = urlparse(raw_db_url)
        query = dict(parse_qsl(parsed.query))
        query["sslmode"] = "require"
        raw_db_url = urlunparse(parsed._replace(query=urlencode(query)))

    app.config["SQLALCHEMY_DATABASE_URI"] = raw_db_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_pre_ping": True,
        "pool_size": 5,
        "max_overflow": 10,
    }

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

    @app.route("/health")
    def health():
        """Health check endpoint - no DB required"""
        return {"status": "ok", "version": "1.0"}, 200

    @app.route("/")
    def index():
        subjects = []
        db_available = False
        
        # Try to create tables on first request if they don't exist
        try:
            db.create_all()
        except Exception as e:
            app.logger.warning(f"Failed to create tables: {e}")
        
        try:
            # Check if questions exist in DB
            count = Question.query.count()
            if count == 0:
                try:
                    import_sheet_questions()
                except Exception as e:
                    app.logger.warning(f"Failed to import sheet: {e}")

            # Get distinct subjects
            subjects = [
                {"angi": row[0], "hicheel": row[1]}
                for row in Question.query.with_entities(Question.angi, Question.hicheel)
                    .distinct().order_by(Question.angi, Question.hicheel).all()
            ]
            db_available = True
        except Exception as e:
            app.logger.error(f"Error in index DB query: {e}", exc_info=True)
            subjects = []

        progress_stats = []
        if current_user.is_authenticated and db_available:
            try:
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
            except Exception as e:
                app.logger.error(f"Error getting progress: {e}", exc_info=True)
                progress_stats = []

        try:
            return render_template("index.html", progress_stats=progress_stats, subjects=subjects)
        except Exception as e:
            app.logger.error(f"Error rendering template: {e}", exc_info=True)
            return "<html><head><title>Error</title></head><body>Template rendering failed</body></html>", 500

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

# Don't call db.create_all() at startup on Render - it causes timeouts
# Tables will be created on first request if needed
# with app.app_context():
#     try:
#         db.create_all()
#     except Exception as exc:
#         print("Warning: failed to create tables at startup:", exc)

if __name__ == '__main__':
    app.run(debug=True)
