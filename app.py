import os
import google.generativeai as genai
from flask import Flask, render_template, request, redirect, url_for

# Gemini API тохиргоо (Render дээр Environment Variable болгож тавих эсвэл шууд түлхүүрээ бичих)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "ЭНД_ӨӨРИЙН_GEMINI_API_KEY_ТАВИНА")
genai.configure(api_key=GEMINI_API_KEY)

# ... (Таны өмнөх бусад кодууд хэвээрээ байна)

# 6. Хиймэл оюуны хайлтын зам
@app.route('/ai-search', methods=['POST'])
def ai_search():
    user_prompt = request.form.get('prompt')
    if not user_prompt:
        return redirect(url_for('index'))
        
    try:
        # Сурагчдад зөв хариулах AI-ийн дүрмийн тохиргоо
        system_instruction = (
            "Чи бол Super Brain системийн ухаалаг AI туслах багш байна. "
            "Сурагчид чамаас мэргэжил сонголт, шалгалтын сэдэв, монгол/англи хэлний дүрэм, "
            "болон математик/физикийн томьёо асууна. Чи хариултыг маш тодорхой, ойлгомжтой, "
            "сурагчдад урам зориг өгөхүйцээр, цэгцтэй (bullet points ашиглан) монгол хэлээр хариулна уу."
        )
        
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=system_instruction
        )
        
        response = model.generate_content(user_prompt)
        ai_response = response.text
        
    except Exception as e:
        ai_response = f"Уучлаарай, AI системтэй холбогдоход алдаа гарлаа: {str(e)}"
        
    return render_template('ai_result.html', prompt=user_prompt, response=ai_response)