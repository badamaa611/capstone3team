from flask import Blueprint, jsonify, request
from flask_login import login_required
import pandas as pd
import os

test_bp = Blueprint("test", __name__)

# Таны CSV файлын зам (Төслийн үндсэн хавтаст байгаа гэж тооцов)
CSV_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "capstone data - Sheet1.csv")

@test_bp.route("/questions", methods=["GET"])
@login_required
def get_questions():
    """Фронт талын нэхэж буй /api/questions хаяг энд байна"""
    # URL-ээс ирж буй параметрийг унших (Жишээ нь: angi=12, hicheel=Англи хэл)
    angi_param = request.args.get("angi")
    hicheel_param = request.args.get("hicheel")

    if not angi_param or not hicheel_param:
        return jsonify({"error": "Анги болон хичээлийн мэдээлэл дутуу байна.", "questions": []}), 400

    # CSV файл байгаа эсэхийг шалгах
    if not os.path.exists(CSV_FILE_PATH):
        return jsonify({"error": f"CSV файл олдсонгүй: {CSV_FILE_PATH}", "questions": []}), 404

    try:
        # CSV файлыг унших
        df = pd.read_csv(CSV_FILE_PATH)
        
        # Баганын нэрсийг цэвэрлэх (зайг устгах)
        df.columns = df.columns.str.strip()
        
        # Анги болон Хичээлээр нь шүүх
        # Тэмдэгт болон Тоон төрлийг зөрөхөөс сэргийлж string болгож харьцуулна
        filtered_df = df[
            (df['Анги'].astype(str) == str(angi_param)) & 
            (df['Хичээл'].astype(str).str.strip() == str(hicheel_param).strip())
        ]
        
        questions_list = []
        for _, row in filtered_df.iterrows():
            # Найдвартай байх үүднээс аль ч нэршлээр байсан уншихаар тохируулав
            questions_list.append({
                "asuult": str(row.get("Асуулт", row.get("asuult", ""))),
                "link": str(row.get("link", row.get("Линк", ""))) if pd.notna(row.get("link")) else "",
                "zow_hariult": str(row.get("зөв хариулт", row.get("zow_hariult", ""))),
                "a_hariu": str(row.get("Буруу хариулт 1", row.get("a_hariu", ""))),
                "b_hariu": str(row.get("Буруу хариулт 2", row.get("b_hariu", ""))),
                "v_hariu": str(row.get("Буруу хариулт 3", row.get("v_hariu", "")))
            })
            
        # Сонгосон анги, хичээлд асуулт олдоогүй бол
        if not questions_list:
            return jsonify({"message": "Тохирох асуулт олдсонгүй.", "questions": []}), 200

        # Амжилттай бол асуултуудыг буцаана
        return jsonify({"questions": questions_list}), 200

    except Exception as e:
        return jsonify({"error": f"Серверийн алдаа: {str(e)}", "questions": []}), 500