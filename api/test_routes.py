from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
import random

test_bp = Blueprint("test", __name__)

@test_bp.route("/test/generate")
@login_required
def generate_test():
    """
    Blueprint-ийн харьцаагаар рандом тест үүсгэх
    GET /api/test/generate?angi=12&hicheel=Биологи&too=30
    """
    angi    = request.args.get("angi", "12")
    hicheel = request.args.get("hicheel", "")
    too     = int(request.args.get("too", 30))

    # Blueprint харьцаа: 27% мэдлэг, 53% чадвар, 20% хэрэглээ
    medleg  = round(too * 0.27)
    chadwar = round(too * 0.53)
    heregel = too - medleg - chadwar

    # TODO: DB-ээс татах
    # questions = Question.query.filter_by(angi=angi, hicheel=hicheel)...
    return jsonify({
        "angi": angi,
        "hicheel": hicheel,
        "niit": too,
        "huwiari": {"medleg": medleg, "chadwar": chadwar, "heregel": heregel},
        "asuultuud": []  # DB холбосны дараа дүүргэнэ
    })

@test_bp.route("/test/submit", methods=["POST"])
@login_required
def submit_test():
    """
    Тестийн хариулт илгээх
    POST /api/test/submit
    Body: { session_id, answers: [{question_id, hariult}] }
    """
    data = request.get_json()
    # TODO: хариулт шалгаж, алдаатай сэдвийг бүртгэх
    return jsonify({"status": "ok", "onoo": 0})
