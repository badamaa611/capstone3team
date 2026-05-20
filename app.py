import os
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_dance.contrib.google import make_google_blueprint, google

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "super-secret-key-12345")

raw_db_url = os.environ.get("DATABASE_URL", "sqlite:///users.db")
if raw_db_url.startswith("postgres://"):
    raw_db_url = raw_db_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = raw_db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "google.login"

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ner = db.Column(db.String(100))
    email = db.Column(db.String(120), unique=True, nullable=False)
    nuuts_ug = db.Column(db.String(100))
    duwer = db.Column(db.String(20), default="suragch")

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
    email = info["email"]
    ner = info.get("name", "Хэрэглэгч")
    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(ner=ner, email=email, nuuts_ug="google-auth", duwer="suragch")
        db.session.add(user)
        db.session.commit()
    login_user(user)
    return redirect(url_for("index"))

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

@app.route("/")
def index():
    return render_template("index.html")

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)