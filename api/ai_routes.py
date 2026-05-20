from flask import Blueprint, jsonify, request
from flask_login import login_required
import os, json

try:
    import google.generativeai as genai
except ImportError:
    genai = None

ai_bp = Blueprint("ai", __name__)

@ai_bp.route("/generate-questions", methods=["POST"])
@login_required
def generate_questions():
    data    = request.get_json() or {}
    angi    = data.get("angi", "12")
    sedew   = data.get("sedew", "")
    hicheel = data.get("hicheel", "")
    too     = int(data.get("too", 3))

    api_key = os.getenv("GOOGLE_API_KEY", "")
    if not genai or not api_key:
        return jsonify({
            "error": "Gemini API not configured. Set GOOGLE_API_KEY and install google-generativeai."
        }), 500

    genai.configure(api_key=api_key)
    model_name = os.getenv("GOOGLE_GEMINI_MODEL", "models/gemini-1.5-mini")
    model = genai.GenerativeModel(model_name)

    prompt = (
        f"Та Монгол улсын ерөнхий боловсролын {angi}-р ангийн {hicheel} хичээлийн "
        f"{sedew} сэдвээр {too} олон сонголтот асуулт үүсгэнэ үү.\n\n"
        "Зөвхөн дараах JSON массив форматаар буцаана уу, өөр текст огт оруулахгүй:\n"
        "[\n"
        "  {\"asuult\": \"Асуултын текст энд\",\n"
        "    \"a_hariu\": \"А хариулт\",\n"
        "    \"b_hariu\": \"Б хариулт\",\n"
        "    \"v_hariu\": \"В хариулт\",\n"
        "    \"g_hariu\": \"Г хариулт\",\n"
        "    \"zow_hariult\": \"A\",\n"
        "    \"tuwshin\": 2\n"
        "  }\n"
        "]"
    )

    try:
        chat = genai.ChatSession(model)
        response = chat.send_message(prompt)
        text = getattr(response, "text", None) or getattr(response, "content", None) or ""
        asuultuud = json.loads(text)
    except Exception as exc:
        return jsonify({"error": f"Gemini request failed: {exc}"}), 500

    return jsonify({"asuultuud": asuultuud})
