from flask import Blueprint, jsonify, request
from flask_login import login_required
import anthropic, os, json

ai_bp = Blueprint("ai", __name__)

@ai_bp.route("/generate-questions", methods=["POST"])
@login_required
def generate_questions():
    data    = request.get_json()
    angi    = data.get("angi", "12")
    sedew   = data.get("sedew", "")
    hicheel = data.get("hicheel", "")
    too     = data.get("too", 3)

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY", ""))

    prompt = f"""Та Монгол улсын ерөнхий боловсролын {angi}-р ангийн {hicheel} хичээлийн 
"{sedew}" сэдвээр {too} олон сонголтот асуулт үүсгэнэ үү.

Зөвхөн дараах JSON массив форматаар буцаана уу, өөр текст огт оруулахгүй:
[
  {{
    "asuult": "Асуултын текст энд",
    "a_hariu": "А хариулт",
    "b_hariu": "Б хариулт", 
    "v_hariu": "В хариулт",
    "g_hariu": "Г хариулт",
    "zow_hariult": "A",
    "tuwshin": 2
  }}
]"""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )

    try:
        asuultuud = json.loads(message.content[0].text)
    except:
        asuultuud = []

    return jsonify({"asuultuud": asuultuud})
