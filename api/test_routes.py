from flask import Blueprint, jsonify, request
from flask_login import login_required
import pandas as pd
import os

test_bp = Blueprint("test", __name__)

CSV_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "capstone data - Sheet1.csv")

@test_bp.route("/questions", methods=["GET"])
@login_required
def get_questions():
    angi_param = request.args.get("angi")
    hicheel_param = request.args.get("hicheel")

    if not angi_param or not hicheel_param:
        return jsonify({"error": "Анги болон хичээлийн мэдээлэл дутуу байна.", "questions": []}), 400

    if not os.path.exists(CSV_FILE_PATH):
        return jsonify({"error": f"CSV файл олдсонгүй", "questions": []}), 404

    try:
        # CSV уншихдаа бүх баганыг текст (string) болгож унших нь төрөл зөрөх алдаанаас сэргийлнэ
        df = pd.read_csv(CSV_FILE_PATH, dtype=str)
        
        # Баганы нэрсийг цэвэрлэх
        df.columns = df.columns.str.strip()
        
        # Хоосон мөрүүдийг хоосон тэмдэгтээр солих (NaN алдаанаас сэргийлнэ)
        df = df.fillna("")
        
        # Анги болон хичээлээр шүүх
        filtered_df = df[
            (df['Анги'].astype(str).str.strip() == str(angi_param).strip()) & 
            (df['Хичээл'].astype(str).str.strip() == str(hicheel_param).strip())
        ]
        
        questions_list = []
        for _, row in filtered_df.iterrows():
            # Зарим мөрөн дээр Буруу хариулт 3 байхгүй байвал хоосон текст авна
            w3 = row.get("Буруу хариулт 3", row.get("Буруу хариулт 3.", ""))
            
            questions_list.append({
                "asuult": str(row.get("Асуулт", "")),
                "link": str(row.get("link", "")),
                "zow_hariult": str(row.get("зөв хариулт", "")),
                "a_hariu": str(row.get("Буруу хариулт 1", "")),
                "b_hariu": str(row.get("Буруу хариулт 2", "")),
                "v_hariu": str(w3 if w3 else "")  # В хариулт дээр сурагчийн фронт хүлээж авдаг
            })
            
        return jsonify({"questions": questions_list}), 200

    except Exception as e:
        # Яг ямар алдаа гарч байгааг JSON хариунд харуулж оношлох
        return jsonify({"error": f"Серверийн алдаа: {str(e)}", "questions": []}), 500