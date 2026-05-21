import os
import random
import google.genai as genai  # Шинэ google.genai сан руу шилжүүлэв
from flask import Blueprint, jsonify, request
from flask_login import login_required
from extensions import db
from models import Question

test_bp = Blueprint('test', __name__)

@test_bp.route('/get-questions', methods=['GET'])
@login_required
def get_questions():
    """Фронтэндоос ирсэн анги, хичээлээр баазаас жинхэнэ асуултуудыг шүүж гаргах"""
    angi = request.args.get('angi', '').strip()
    hicheel = request.args.get('hicheel', '').strip()
    
    questions = []
    
    try:
        # 1. Алхам: Анги болон Хичээл хоёулаа таарч буй жинхэнэ асуултуудыг шүүнэ
        if angi and hicheel:
            # Текст болон тоон хэлбэрээр аль алинаар нь шалгах уян хатан шүүлт
            questions = Question.query.filter(
                (Question.angi == str(angi)) & 
                (Question.hicheel.ilike(f"%{hicheel}%"))
            ).limit(10).all()
        
        # 2. Алхам: Хэрэв хичээлээр олдохгүй бол тухайн ангийн асуултуудаас уншина
        if not questions and angi:
            questions = Question.query.filter_by(angi=str(angi)).limit(10).all()
            
        # 3. Алхам: Тэгээд ч олдохгүй бол баазад байгаа хамгийн эхний 10 асуултыг шавхаж гаргана
        if not questions:
            questions = Question.query.limit(10).all()
            
    except Exception as e:
        # Баазын хүснэгт үүсээгүй эсвэл алдаа гарвал лог дээр хэвлээд цааш үргэлжлүүлнэ
        print(f"Баазаас асуулт уншихад алдаа гарлаа: {e}")
        questions = []

    # 4. Алхам: Хэрэв бааз бүрмөсөн хоосон хэвээр байвал сурагчийг гацаахгүйн тулд түр системээс харуулна
    if not questions:
        return jsonify({
            "questions": [
                {
                    "id": 999,
                    "asuult": f"Уучлаарай, {angi}-р ангийн '{hicheel}' хичээлийн асуулт баазад хараахан ороогүй байна. (Багш Google Sheet-ээс импортлох шаардлагатай)",
                    "sedew": "Системийн мэдэгдэл",
                    "choices": [
                        {"text": "Ойлголоо, багшид мэдэгдэе", "is_correct": True},
                        {"text": "Дахин ачааллах", "is_correct": False},
                        {"text": "Буцах", "is_correct": False},
                        {"text": "Өөр хичээл сонгох", "is_correct": False}
                    ]
                }
            ]
        })

    output = []
    for q in questions:
        # Баазын баганын нэрсийг (asuult/asuult_text, zow/zow_hariult) уян хатан унших хамгаалалт
        asuult_txt = getattr(q, 'asuult_text', None) or getattr(q, 'asuult', 'Асуултын текст олдсонгүй')
        zow_ans = getattr(q, 'zow_hariult', None) or getattr(q, 'zow', None) or getattr(q, 'zow_hariult1', 'Зөв хариулт')
        b1 = getattr(q, 'buruu_hariult1', None) or getattr(q, 'buruu1', 'Буруу хариулт 1')
        b2 = getattr(q, 'buruu_hariult2', None) or getattr(q, 'buruu2', 'Буруу хариулт 2')
        b3 = getattr(q, 'buruu_hariult3', None) or getattr(q, 'buruu3', 'Буруу хариулт 3')
        sedew_ner = getattr(q, 'sedew', 'Ерөнхий сэдэв') or 'Ерөнхий сэдэв'

        choices = [
            {"text": zow_ans, "is_correct": True},
            {"text": b1, "is_correct": False},
            {"text": b2, "is_correct": False},
            {"text": b3, "is_correct": False}
        ]
        # Сурагч бүрт хариултын байрлалыг солиж холих
        random.shuffle(choices)
        
        output.append({
            "id": q.id,
            "asuult": asuult_txt,
            "sedew": sedew_ner,
            "choices": choices
        })
        
    return jsonify({"questions": output})


@test_bp.route('/submit-test', methods=['POST'])
@login_required
def submit_test():
    """Шалгалтын үр дүнг тооцож, алдсан сэдвээр Gemini AI-аар бататгах дасгал үүсгэх"""
    data = request.json or {}
    answers = data.get('answers', [])
    
    zow_too = 0
    buruu_too = 0
    aldsan_sedwuwd = set()
    
    for ans in answers:
        q_id = ans.get('question_id')
        selected = ans.get('selected_text')
        
        if q_id == 999:
            zow_too += 1
            continue
            
        try:
            q = Question.query.get(q_id)
            if q:
                zow_ans = getattr(q, 'zow_hariult', None) or getattr(q, 'zow', '')
                sedew_ner = getattr(q, 'sedew', 'Ерөнхий сэдэв') or 'Ерөнхий сэдэв'
                
                if str(zow_ans).strip() == str(selected).strip():
                    zow_too += 1
                else:
                    buruu_too += 1
                    aldsan_sedwuwd.add(sedew_ner)
        except Exception:
            buruu_too += 1
                    
    if aldsan_sedwuwd:
        sedew_str = ", ".join(list(aldsan_sedwuwd))
        prompt = (
            f"Чи бол Super Brain системийн ухаалаг AI багш байна. Сурагч тест өгөөд дараах сэдвүүд дээр алдсан байна: {sedew_str}.\n"
            f"Эдгээр сэдэв тус бүрээр сурагчийн мэдлэгийг бататгах зорилгоор сонгох хувилбартай (MCQ) шинээр 2 асуулт зохиож өгнө үү.\n"
            f"Асуулт бүрийн доор зөв хариултыг нь заавал тэмдэглэж, тайлбарыг Монгол хэлээр маш тодорхой харуулна уу."
        )
        
        try:
            # Сүүлийн үеийн google-genai сангийн дуудлага
            client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )
            ai_output = response.text
        except Exception as e:
            ai_output = f"Тестийн хариу амжилттай тооцогдлоо. Гэвч AI зөвлөхтэй холбогдоход алдаа гарлаа: {e}"
    else:
        ai_output = "🎉 Төгс гүйцэтгэл! Та бүх асуултандаа 100% зөв хариуллаа. Маш сайн байна!"

    return jsonify({
        "status": "success",
        "zow_too": zow_too,
        "buruu_too": buruu_too,
        "niit_asuult": len(answers) if answers else (zow_too + buruu_too),
        "ai_recommendation": ai_output
    })