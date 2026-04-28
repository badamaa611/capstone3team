from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    login_manager.login_view = "auth.login"

    # Blueprint-уудыг бүртгэх
    from api.auth_routes import auth_bp
    from api.test_routes import test_bp
    from api.ai_routes import ai_bp
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(test_bp, url_prefix="/api")
    app.register_blueprint(ai_bp,   url_prefix="/api/ai")

    # Нүүр хуудас
    @app.route("/")
    def index():
        return render_template("index.html")

    with app.app_context():
        db.create_all()

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
