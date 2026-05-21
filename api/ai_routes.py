from flask import Blueprint, jsonify, request
from flask_login import login_required
import os
import json

try:
    import google.generativeai as genai
except ImportError:
    genai = None

ai_bp = Blueprint("ai", __name__)

@ai_bp.route("/generate-questions", methods=["POST"])
@login_required
def generate_questions():
    """Сэдвийн дагуу шинээр олон сонголтот тест үүсгэх API"""
    data    = request.get_json() or {}
    angi    = data.get("angi", "12")
    sedew   = data.get("sedew", "")
    hicheel = data.get("hicheel", "")
    too     = int(data.get("too", 3))

    # Системийн Environment variable-оос түлхүүрүүдийг унших
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY", "")
    if not genai or not api_key:
        return jsonify({
            "error": "Gemini API тохируулагдаагүй байна. GOOGLE_API_KEY-ийг шалгана уу."
        }), 500

    genai.configure(api_key=api_key)
    # Зөв моделийн нэр: gemini-1.5-flash
    model_name = os.getenv("GOOGLE_GEMINI_MODEL", "gemini-1.5-flash")
    model = genai.GenerativeModel(model_name)

    prompt = (
        f"Та Монгол улсын ерөнхий боловсролын {angi}-р ангийн {hicheel} хичээлийн "
        f"{sedew} сэдвээр {too} олон сонголтот асуулт үүсгэнэ үү.\n\n"
        "Зөвхөн дараах JSON массив форматаар буцаана уу, өөр текст огт оруулахгүй:\n"
        "[\n"
        "  {{\n"
        "    \"asuult\": \"Асуултын текст энд\",\n"
        "    \"a_hariu\": \"А хариулт\",\n"
        "    \"b_hariu\": \"Б хариулт\",\n"
        "    \"v_hariu\": \"В хариулт\",\n"
        "    \"g_hariu\": \"Г хариулт\",\n"
        "    \"zow_hariult\": \"A\",\n"
        "    \"tuwshin\": 2\n"
        "  }}\n"
        "]"
    )

    try:
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        text = response.text
        asuultuud = json.loads(text)
    except Exception as exc:
        return jsonify({"error": f"Gemini асуулт үүсгэхэд алдаа гарлаа: {exc}"}), 500

    return jsonify({"asuultuud": asuultuud})


@ai_bp.route("/generate-adaptive-question", methods=["POST"])
@login_required
def generate_adaptive_question():
    """Сурагч тест дээр алдах үед ижил сэдвийн дагуу бататгал асуулт үүсгэх шинэ API"""
    data = request.get_json() or {}
    wrong_question = data.get("question", "")
    hicheel = data.get("hicheel", "")
    angi = data.get("angi", "12")

    if not wrong_question:
        return jsonify({"error": "Алдсан асуултын текст байхгүй байна."}), 400

    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY", "")
    if not genai or not api_key:
        return jsonify({"error": "Gemini API тохируулагдаагүй байна."}), 500

    genai.configure(api_key=api_key)
    model_name = os.getenv("GOOGLE_GEMINI_MODEL", "gemini-1.5-flash")
    model = genai.GenerativeModel(model_name)

    prompt = (
        f"Чи бол Монгол улсын ЕБС-ийн чадварлаг багш юм. Сурагч {angi}-р ангийн \"{hicheel}\" хичээлийн "
        f"шалгалт өгч байхдаа дараах асуултанд БУРУУ хариулсан тул тухайн сэдвийг нь бататгах "
        f"яг ижил түвшний, ОЙРОЛЦОО өөр нэг шинэ сонголттой асуулт үүсгэж өгнө үү.\n\n"
        f"Алдсан асуулт: \"{wrong_question}\"\n\n"
        "Хариултыг заавал дараах JSON форматаар буцааж, өөр сул үг, тайлбар битгий бич:\n"
        "{\n"
        "  \"asuult\": \"Шинэ зохиосон асуултын текст энд\",\n"
        "  \"a_hariu\": \"А сонголт\",\n"
        "  \"b_hariu\": \"Б сонголт\",\n"
        "  \"v_hariu\": \"В сонголт\",\n"
        "  \"g_hariu\": \"Г сонголт\",\n"
        "  \"zow_hariult\": \"A\"\n"
        "}"
    )

    try:
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        ai_question = json.loads(response.text)
        return jsonify({"status": "success", "data": ai_question}), 200
    except Exception as exc:
        return jsonify({"status": "error", "message": f"Gemini adaptive failed: {exc}"}), 500