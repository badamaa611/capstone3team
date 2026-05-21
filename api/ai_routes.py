import os
from flask import Blueprint, jsonify, request
from flask_login import login_required
from google import genai  # Шинэчлэгдсэн Google GenAI сан

ai_bp = Blueprint('ai', __name__)

# Шинэ тохиргооны дагуу Client үүсгэх
# Render дээрх GEMINI_API_KEY хувьсагчаас автоматаар уншина
client = genai.Client()

@ai_bp.route('/ai-chat', methods=['POST'])
@login_required
def ai_chat():
    """Сурагчтай ерөнхий байдлаар харилцах эсвэл тусламж үзүүлэх AI чат"""
    data = request.json or {}
    user_message = data.get('message', '').strip()
    
    if not user_message:
        return jsonify({"status": "error", "message": "Зурвас хоосон байна."}), 400
        
    try:
        # Шинэ сангийн дагуу gemini-2.5 буюу хамгийн сүүлийн загварыг ашиглах
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_message
        )
        return jsonify({
            "status": "success",
            "reply": response.text
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"AI хариу өгөхөд алдаа гарлаа: {str(e)}"
        }), 500