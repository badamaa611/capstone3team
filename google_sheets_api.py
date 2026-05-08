"""
google_sheets_api.py — Google Sheet-ээс асуултуудыг уншиж, DB-д оруулах

Суулгах:
  pip install --break-system-packages google-auth-oauthlib google-auth-httplib2 google-api-python-client

Ашиглах:
  python google_sheets_api.py
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
from google.auth.oauthlib.flow import InstalledAppFlow
import gspread
from app import create_app, db
from models import Question

SHEET_ID = "1HkJZUebgNFtYghS55KUKcCjNVx7A4O2huEvyv1d331o"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

def get_sheet_data():
    """
    Google Sheet-ээс асуултуудыг уншина
    """
    try:
        # Үзэл баримтлалын хувьд, энэ төлөвлөгөөнд бид
        # публик sheet ашигладаг, үнэдлэх хэрэгтэй болохгүй
        import gspread
        from gspread_dataframe import get_as_dataframe
        
        # Хэрэв приватт sheet бол OAuth2 хэрэгтэй
        # Одоохондоо энгийн HTTP request ашигла
        
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
        import pandas as pd
        df = pd.read_csv(url)
        return df
    except Exception as e:
        print(f"Sheet уншихад алдаа: {e}")
        print("Дараах URL-ээс таблиц татаж авна уу:")
        print(f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv")
        return None

def import_questions(df):
    """
    DataFrame-ээс асуултуудыг DB-д оруулна
    """
    app = create_app()
    
    with app.app_context():
        added = 0
        for idx, row in df.iterrows():
            # Баганын нэрс сэдэв сэдвүүдээ тохируулах
            task = row.get('task', '')
            link = row.get('link', '')
            zow_hariult = row.get('зөв хариулт', '')
            angi = str(row.get('Аль анги вэ?', '12'))
            hicheel = row.get('Хичээл', '')
            buruuh1 = row.get('Буруу хариулт 1', '')
            buruuh2 = row.get('Буруу хариулт 2', '')
            buруuh3 = row.get('Буруу хариулт 3', '')
            
            if not task or not hicheel:
                continue
            
            # Түвшин сониход нар хуваарилах (санал болгох)
            tuwshin = 2  # дефолт
            if any(keyword in task.lower() for keyword in ['нэрлэ', 'тодорхойл', 'жагса', 'таних']):
                tuwshin = 1
            elif any(keyword in task.lower() for keyword in ['шинжил', 'дүгнэ', 'үнэл']):
                tuwshin = 3
            
            # Асуулт DB-д оруулах
            q = Question(
                angi=angi,
                hicheel=hicheel,
                sedew=hicheel,  # сэдэв нь хичээлтэй адил гэж авна
                asuult=task,
                a_hariu=zow_hariult,
                b_hariu=buruuh1,
                v_hariu=buruuh2,
                g_hariu=buруuh3,
                d_hariu=link if link else '',
                zow_hariult='A',  # A нь зөв хариулт
                tuwshin=tuwshin,
            )
            db.session.add(q)
            added += 1
        
        db.session.commit()
        print(f"✅ {added} асуулт нэмэгдлээ")

if __name__ == "__main__":
    print("Google Sheet-ээс асуултуудыг уншиж байна...")
    df = get_sheet_data()
    
    if df is not None:
        print(f"Sheet-ээс {len(df)} мөр уншилаа")
        import_questions(df)
    else:
        print("Sheet-ийг татаж авахад алдаа гарлаа")
