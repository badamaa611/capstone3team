import csv
import requests
from flask import Blueprint, jsonify, current_app
from extensions import db
from models import Question

import_bp = Blueprint('import', __name__)

# ⚠️ БАГШ АА: Өөрийн Google Sheet-ийн урт ID-г энд орлуулан тавиарай!
# Жишээ нь: https://docs.google.com/spreadsheets/d/1xxXXxx_XXxx/edit бол ID нь "1xxXXxx_XXxx" байна.
GOOGLE_SHEET_ID = "1xxXXxx_XXxx_ЭНД_ӨӨРИЙН_SHEET_ID_Г_ТАВИАРАЙ"

@import_bp.route('/import-now', methods=['GET'])
def import_from_sheet():
    """Google Sheet-ээс асуултуудыг татаж, баазыг шинэчлэх ухаалаг функц"""
    # Google Sheet-ийг шууд CSV хэлбэрээр татах ухаалаг холбоос
    csv_url = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/export?format=csv&gid=0"
    
    try:
        response = requests.get(csv_url)
        if response.status_code != 200:
            return jsonify({
                "status": "error", 
                "message": f"Google Sheet-ээс өгөгдөл татаж чадсангүй. Та Sheet-ээ 'Anyone with the link can view' болгосон уу? Сэргээх код: {response.status_code}"
            }), 400
            
        # CSV текстийг унших
        csv_data = response.content.decode('utf-8').splitlines()
        reader = csv.DictReader(csv_data)
        
        # Баазад байгаа хуучин асуултуудыг цэвэрлэх (Давхардахаас сэргийлнэ)
        try:
            db.session.query(Question).delete()
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Хуучин баазыг цэвэрлэхэд алдаа гарлаа: {e}")

        success_count = 0
        skipped_count = 0
        
        for row in reader:
            # Sheet-ийн баганын нэрүүдийг уян хатан шалгах (Том жижиг үсэг, зайг цэвэрлэх)
            row = {k.strip().lower() if k else '': v for k, v in row.items()}
            
            # Асуултын үндсэн текстийг олох (asuult эсвэл asuult_text)
            asuult_txt = row.get('asuult') or row.get('asuult_text') or row.get('asuult_text1')
            if not asuult_txt:
                skipped_count += 1
                continue
                
            # Бусад өгөгдлүүдийг Sheet-ээс унших
            angi = row.get('angi', '12').replace('-р анги', '').replace('анги', '').strip()
            hicheel = row.get('hicheel', 'Ерөнхий').strip()
            sedew = row.get('sedew', 'Ерөнхий сэдэв').strip()
            
            zow = row.get('zow') or row.get('zow_hariult') or row.get('zow_hariult1')
            b1 = row.get('buruu1') or row.get('buruu_hariult1')
            b2 = row.get('buruu2') or row.get('buruu_hariult2')
            b3 = row.get('buruu3') or row.get('buruu_hariult3')
            
            # Шинэ асуултыг бааз руу бэлдэх
            new_q = Question(
                angi=str(angi),
                hicheel=hicheel,
                sedew=sedew,
                asuult_text=asuult_txt,  # Таны Моделд asuult гэж байвал asuult=asuult_txt болгоорой
                zow_hariult=zow if zow else "Зөв хариулт олдсонгүй",
                buruu_hariult1=b1 if b1 else "Буруу хувилбар 1",
                buruu_hariult2=b2 if b2 else "Буруу хувилбар 2",
                buruu_hariult3=b3 if b3 else "Буруу хувилбар 3"
            )
            
            db.session.add(new_q)
            success_count += 1
            
        db.session.commit()
        return jsonify({
          "status": "success", 
          "message": f"Super Brain бааз амжилттай шинэчлэгдлээ!", 
          "imported_questions_count": success_count,
          "skipped_rows": skipped_count
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": f"Импорт хийх явцад алдаа гарлаа: {str(e)}"}), 500