import os
import random
import google.generativeai as genai
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from extensions import db
from models import Question, TestSession, TestAnswer, WeakTopic

test_bp = Blueprint('test', __name__)

# Gemini API түлхүүрийг орчноос унших
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

@test_bp.route('/get-questions', methods=['GET'])
@login_required
def get_questions():
    """Баазаас асуултуудыг аваад хариултуудыг нь хольж илгээх"""
    angi = request.args.get('angi', '12')
    hicheel = request.args.get('hicheel', '')
    
    # Сонгосон анги, хичээлээр шүүнэ
    questions = Question.query.filter_by(angi=angi, hicheel=hicheel).limit(10).all()
    
    if not questions:
        # Хэрэв тухайн хичээлээр олдохгүй бол ангийнх нь дурын асуултаас харуулна
        questions = Question.query.filter_by(angi=angi).limit(10).all()

    output = []
    for q in questions:
        # Хариултуудыг нэг жагсаалтад цуглуулах
        choices = [
            {"text": q.zow_hariult, "is_correct": True},
            {"text": q.buruu_hariult1, "is_correct": False},
            {"text": q.buruu_hariult2, "is_correct": False},
            {"text": q.buruu_hariult3, "is_correct": False}
        ]
        # Хариултуудыг санамсаргүйгээр доор дээр нь оруулж холих
        random.shuffle(choices)
        
        # 'sedew' багана байхгүй бол алдаа гаргахгүй байх хамгаалалт
        sedew_ner = getattr(q, 'sedew', 'Ерөнхий сэдэв')
        if not sedew_ner:
            sedew_ner = "Ерөнхий сэдэв"
            
        output.append({
            "id": q.id,
            "asuult": q.asuult_text,
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
        
        q = Question.query.get(q_id)
        if q:
            is_correct = (q.zow_hariult == selected)
            if is_correct:
                zow_too += 1
            else:
                buruu_too += 1
                sedew_ner = getattr(q, 'sedew', 'Ерөнхий сэдэв')
                if sedew_ner:
                    aldsan_sedwuwd.add(sedew_ner)
                    
    # Gemini AI ашиглан бататгах асуулт үүсгэх
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
            ai_output = "Тестийн хариу амжилттай тооцогдлоо. Гэвч Gemini AI-аас асуулт дуудахад алдаа гарлаа. Хичээлээ сайн давтаарай!"
    else:
        ai_output = "🎉 Баяр хүргэе! Та бүх асуултандаа зөв хариулж, 100% амжилт үзүүллээ."

    return jsonify({
        "status": "success",
        "zow_too": zow_too,
        "buruu_too": buruu_too,
        "niit_asuult": len(answers) if answers else (zow_too + buruu_too),
        "ai_recommendation": ai_output
    })