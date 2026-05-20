from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from extensions import db
from models import Question, TestSession, TestAnswer, WeakTopic
from google_sheets_api import import_sheet_questions, append_test_result
import random
from datetime import datetime
from sqlalchemy import text
import os, json

try:
    import google.generativeai as genai
except Exception:
    genai = None

# DB migration — image_url багана нэмэх
def migrate_db(app):
    with app.app_context():
        try:
            db.session.execute(text("ALTER TABLE questions ADD COLUMN image_url VARCHAR(500)"))
            db.session.commit()
            print("✅ image_url багана нэмэгдлээ")
        except Exception as e:
            print(f"Migration: {e}")
test_bp = Blueprint("test", __name__)

@test_bp.route("/test/generate")
@login_required
def generate_test():
    angi    = request.args.get("angi", "12")
    hicheel = request.args.get("hicheel", "")
    too     = int(request.args.get("too", 30))

    if Question.query.count() == 0 or Question.query.filter(Question.angi == angi).count() == 0:
        import_sheet_questions()

    # Blueprint харьцаа: 27% мэдлэг, 53% чадвар, 20% хэрэглээ
    medleg_too  = round(too * 0.27)
    chadwar_too = round(too * 0.53)
    heregel_too = too - medleg_too - chadwar_too

    def get_questions(tuwshin, count):
        subject = hicheel.strip()
        q = Question.query.filter(
            Question.angi == angi,
            Question.tuwshin == tuwshin,
            Question.hicheel.ilike(f"%{subject}%")
        ).all()
        if len(q) < count:
            q = Question.query.filter(
                Question.angi == angi,
                Question.hicheel.ilike(f"%{subject}%")
            ).all()
        if len(q) < count:
            q = Question.query.filter(Question.angi == angi).all()
        return random.sample(q, min(count, len(q)))

    asuultuud = (
        get_questions(1, medleg_too) +
        get_questions(2, chadwar_too) +
        get_questions(3, heregel_too)
    )
    if not asuultuud:
        # Хичээл олдохгүй бол анги дээрээс суурь асуултууд авах
        asuultuud = Question.query.filter(Question.angi == angi).limit(10).all()
    random.shuffle(asuultuud)

    # Remove duplicate questions (some buckets may overlap)
    seen_ids = set()
    unique_qs = []
    for q in asuultuud:
        if q.id not in seen_ids:
            seen_ids.add(q.id)
            unique_qs.append(q)
    asuultuud = unique_qs

    # Тестийн сесс үүсгэх (тоо одоо дүнгэслэгдсэн unique асуултуудаар)
    session = TestSession(
        suragch_id=current_user.id,
        angi=angi, hicheel=hicheel, too=len(asuultuud)
    )
    db.session.add(session)
    db.session.commit()

    return jsonify({
        "session_id": session.id,
        "angi": angi,
        "hicheel": hicheel,
        "niit": len(asuultuud),
        "asuultuud": [q.to_dict() for q in asuultuud]
    })

@test_bp.route("/test/submit", methods=["POST"])
@login_required
def submit_test():
    data       = request.get_json()
    session_id = data.get("session_id")
    answers    = data.get("answers", {})  # {question_id: hariult}

    session = TestSession.query.get(session_id)
    if not session:
        return jsonify({"error": "Session олдсонгүй"}), 404

    onoo = 0
    sul_sedewnuud = {}

    for q_id_str, hariult in answers.items():
        q = Question.query.get(int(q_id_str))
        if not q:
            continue
        zuw = (hariult == q.zow_hariult)
        if zuw:
            onoo += 1
        else:
            # Сул сэдэв бүртгэх
            key = (q.hicheel, q.sedew)
            sul_sedewnuud[key] = sul_sedewnuud.get(key, 0) + 1

        answer = TestAnswer(
            session_id=session_id,
            question_id=q.id,
            ogson_hariult=hariult,
            zuw_esehuu=zuw
        )
        db.session.add(answer)

    # WeakTopic шинэчлэх
    for (hicheel, sedew), aldaa in sul_sedewnuud.items():
        wt = WeakTopic.query.filter_by(
            suragch_id=current_user.id,
            hicheel=hicheel, sedew=sedew
        ).first()
        if wt:
            wt.aldaa_too += aldaa
            wt.updated = datetime.utcnow()
        else:
            wt = WeakTopic(
                suragch_id=current_user.id,
                hicheel=hicheel, sedew=sedew, aldaa_too=aldaa
            )
            db.session.add(wt)

    session.niit_onoo  = onoo
    session.duusah_tsag = datetime.utcnow()
    db.session.commit()

    try:
        append_test_result(current_user.ner, session.angi, session.hicheel, onoo, len(answers))
    except Exception:
        # Swallow sheet-write errors (optional: enable logging to file). Keep response flow intact.
        print("Append to Google Sheet failed")
    # Optionally generate suggested practice questions for weak topics using Gemini
    def generate_ai_questions(angi, hicheel, sedew, too=3):
        api_key = os.getenv("GOOGLE_API_KEY", "")
        if not genai or not api_key:
            return []
        try:
            genai.configure(api_key=api_key)
            model_name = os.getenv("GOOGLE_GEMINI_MODEL", "models/gemini-1.5-mini")
            model = genai.GenerativeModel(model_name)
            prompt = (
                f"Та Монгол улсын ерөнхий боловсролын {angi}-р ангийн {hicheel} хичээлийн "
                f"{sedew} сэдвээр {too} олон сонголтот асуулт үүсгэнэ үү.\n\n"
                "Зөвхөн JSON массив форматаар буцаана уу."
            )
            chat = genai.ChatSession(model)
            response = chat.send_message(prompt)
            text = getattr(response, "text", None) or getattr(response, "content", None) or ""
            return json.loads(text)
        except Exception:
            return []

    sul_list = [
        {"hicheel": h, "sedew": s, "aldaa": a}
        for (h, s), a in sul_sedewnuud.items()
    ]

    suggested = {}
    for (h, s), a in sul_sedewnuud.items():
        # generate up to 3 practice questions per weak topic (best-effort)
        suggested_key = f"{h}||{s}"
        suggested[suggested_key] = generate_ai_questions(session.angi, h, s, too=3)
    return jsonify({
        "onoo": onoo,
        "niit": len(answers),
        "huvi": round(onoo / len(answers) * 100) if answers else 0,
        "sul_sedewnuud": sul_list,
        "suggested_questions": suggested
    })
