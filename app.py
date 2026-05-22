import os
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin
from flask_bcrypt import Bcrypt
from flask import Flask, render_template, request, jsonify
# ... бусад импортууд ...

# AI асуултын зам (Route)
@app.route('/ai-ask', methods=['POST'])
def ai_ask():
    data = request.get_json()
    user_query = data.get('query')
    
    if not user_query:
        return jsonify({"answer": "Асуултаа оруулна уу."})

    try:
        # Энд та өөрийн Gemini API түлхүүрийг ашиглан жинхэнэ хариулт авна.
        # Одоогоор жишээ хариулт буцааж байна.
        ai_response = f"'{user_query}' сэдвийн хүрээнд Superbrain AI зөвлөж байна: Энэхүү сэдэв нь улсын шалгалтын блупринтэд чухал байр суурь эзэлдэг тул тест хэсгээс дэлгэрүүлж үзээрэй."
        return jsonify({"answer": ai_response})
    except Exception as e:
        return jsonify({"answer": f"AI холболтод алдаа гарлаа: {str(e)}"})

# ... бусад кодууд ...
app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-brain-secret-key-2026'

basedir = os.path.abspath(os.path.dirname(__file__))
instance_path = os.path.join(basedir, 'instance')
if not os.path.exists(instance_path):
    os.makedirs(instance_path, exist_ok=True)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(instance_path, 'user.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    ner = db.Column(db.String(150), nullable=False)   
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='suragch') 
    grade = db.Column(db.String(20), nullable=True)                  

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

from auth import auth as auth_blueprint
app.register_blueprint(auth_blueprint, url_prefix='/auth')

with app.app_context():
    db.create_all()

# --- ХУУДАСНУУДЫН ХОЛБООС ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/tests')
def tests():
    # Хэрэв танд tests.html байгаа бол render_template('tests.html') болгоорой
    try:
        return render_template('tests.html')
    except:
        return "<div style='text-align:center; margin-top:50px;'><h3>Шалгалтын бэлтгэл тестүүд (Түр хуудас)</h3><a href='/'>Буцах</a></div>"

@app.route('/ai-chat')
def ai_chat():
    # Хэрэв танд ai-chat.html байгаа бол render_template('ai-chat.html') болгоорой
    try:
        return render_template('ai-chat.html')
    except:
        return "<div style='text-align:center; margin-top:50px;'><h3>AI Зөвлөх систем (Түр хуудас)</h3><a href='/'>Буцах</a></div>"

if __name__ == '__main__':
    app.run(debug=True)
    