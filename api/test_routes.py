import os
import random
import google.generativeai as genai
from flask import Blueprint, jsonify, request
from flask_login import login_required
from extensions import db
from models import Question

test_bp = Blueprint('test', __name__)

# Gemini API тохиргоо
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

@test_bp.route('/get-questions', methods=['GET'])
@login_required
def get_questions():
    """Баазаас асуултуудыг аваад хариултуудыг нь хольж илгээх"""
    angi = request.args.get('angi', '')
    hicheel = request.args.get('hicheel', '')
    
    questions = []
    
    # 1. Хэрэв анги болон хичээл хоёулаа сонгогдсон бол шүүнэ
    if angi and hicheel:
        questions = Question.query.filter_by(angi=str(angi), hicheel=str(hicheel)).limit(10).all()
    
    # 2. Олдохгүй бол зөвхөн ангиар нь шүүж үзнэ
    if not questions and angi:
        questions = Question.query.filter_by(angi=str(angi)).limit(10).all()
        
    # 3. Тэгээд ч олдохгүй бол баазад байгаа хамгийн эхний 10 асуултыг шууд гаргана
    if not questions:
        questions = Question.query.limit(10).all()

    # 4. Бааз бүрмөсөн хоосон үед түр туршиж үзэх демо асуултыг кодон дотроос шууд өгнө
    if not questions:
        return jsonify({
            "questions": [
                {
                    "id": 999,
                    "asuult": "Монгол улсын нийслэл хот юу вэ? (Системийн демо асуулт)",
                    "sedew": "Ерөнхий мэдлэг",
                    "choices": [
                        {"text": "Улаанбаатар", "is_correct": True},
                        {"text": "Дархан", "is_correct": False},
                        {"text": "Эрдэнэт", "is_correct": False},
                        {"text": "Чойбалсан", "is_correct": False}
                    ]
                }
            ]
        })

    output = []
    for q in questions:
        # Баганы нэрс asuult уу эсвэл asuult_text үү гэдгийг уян хатан унших
        asuult_txt = getattr(q, 'asuult_text', None) or getattr(q, 'asuult', 'Асуултын текст олдсонгүй')
        zow_ans = getattr(q, 'zow_hariult', None) or getattr(q, 'zow', 'Зөв хариулт олдсонгүй')
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
        # Хариултуудыг санамсаргүйгээр холих
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
    """Шалгалтын үр дүнг тооцож, алдсан сэдвээр Gemini-ээр асуулт үүсгэх"""
    data = request.json or {}
    answers = data.get('answers', [])
    
    zow_too = 0
    buruu_too = 0
    aldsan_sedwuwd = set()
    
    for ans in answers:
        q_id = ans.get('question_id')
        selected = ans.get('selected_text')
        
        # Демо асуултыг шалгах хэсэг
        if q_id == 999:
            if selected == "Улаанбаатар":
                zow_too += 1
            else:
                buruu_too += 1
                aldsan_sedwuwd.add("Монголын газарзүй")
            continue
            
        q = Question.query.get(q_id)
        if q:
            zow_ans = getattr(q, 'zow_hariult', None) or getattr(q, 'zow', '')
            sedew_ner = getattr(q, 'sedew', 'Ерөнхий сэдэв') or 'Ерөнхий сэдэв'
            
            if zow_ans == selected:
                zow_too += 1
            else:
                buruu_too += 1
                aldsan_sedwuwd.add(sedew_ner)
                    
    if aldsan_sedwuwd:
        sedew_str = ", ".join(list(aldsan_sedwuwd))
        prompt = (
            f"Чи бол Монголын ЕБС-ийн багшид туслах AI байна. Сурагч тест өгөөд дараах сэдвүүд дээр алдсан байна: {sedew_str}.\n"
            f"Эдгээр сэдэв тус бүрээр сурагчийн мэдлэгийг бататгах зорилгоор яг 3, 3 ижил түвшний, сонгох хувилбартай (MCQ) шинэ асуулт зохиож өгнө үү.\n"
            f"Асуулт бүрийн доор зөв хариултыг нь заавал тэмдэглэж, маш тодорхой Монгол хэлээр харуулна уу."
        )
        
        try:
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content(prompt)
            ai_output = response.text
        except Exception as e:
            ai_output = "Тестийн хариу амжилттай тооцогдлоо. Гэвч Gemini AI-тай холбогдоход алдаа гарлаа. Хичээлээ сайн давтаарай!"
    else:
        ai_output = "🎉 Баяр хүргэе! Та бүх асуултандаа зөв хариулж, 100% амжилт үзүүллээ."

    return jsonify({
        "status": "success",
        "zow_too": zow_too,
        "buruu_too": buruu_too,
        "niit_asuult": len(answers) if answers else (zow_too + buruu_too),
        "ai_recommendation": ai_output
    })