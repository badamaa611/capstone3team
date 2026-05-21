import os
import csv
import json
import requests
from io import StringIO
from datetime import datetime
from extensions import db
from models import Question

try:
    import gspread
except ImportError:
    gspread = None

SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "1HkJZUebgNFtYghS55KUKcCjNVx7A4O2huEvyv1d331o")
SHEET_GID = os.getenv("GOOGLE_SHEET_GID", "830552134")
SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "service_account.json")
SERVICE_ACCOUNT_JSON = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "")

_sheet_cache = None
_cache_timestamp = None
CACHE_TTL = 3600  # 1 hour


def get_sheet_csv_url(gid=None):
    gid = gid or SHEET_GID
    return f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid}"


def get_sheet_data(gid=None, use_cache=True):
    """Fetch Sheet data with caching support"""
    global _sheet_cache, _cache_timestamp
    
    # Check cache
    if use_cache and _sheet_cache is not None:
        now = datetime.now().timestamp()
        if _cache_timestamp and (now - _cache_timestamp) < CACHE_TTL:
            return _sheet_cache
    
    url = get_sheet_csv_url(gid)
    # Increased timeout for Render environment
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    text = response.content.decode("utf-8-sig")
    data = list(csv.DictReader(StringIO(text)))
    
    # Cache result
    _sheet_cache = data
    _cache_timestamp = datetime.now().timestamp()
    
    return data

def normalize(value):
    return str(value or "").strip()


def import_sheet_questions():
    global _sheet_cache, _cache_timestamp
    _sheet_cache = None
    _cache_timestamp = None
    rows = get_sheet_data(use_cache=False)
    
    if rows:
        print(f"DEBUG: {len(rows)} мөр уншлаа")
        if rows:
            print(f"DEBUG: Эхний мөрийн түлхүүрүүд: {list(rows[0].keys())}")
    added = 0
    for row in rows:
        task = normalize(row.get("Асуулт") or row.get("task"))
        image_url = normalize(row.get("link"))
        correct_answer = normalize(row.get("зөв хариулт"))
        angi = normalize(row.get("Анги") or row.get("Аль анги вэ?") or row.get("Аль анги", "12"))
        hicheel = normalize(row.get("Хичээл"))
        sedew = normalize(row.get("Сэдэв") or hicheel)
        buruuh1 = normalize(row.get("Буруу хариулт 1"))
        buruuh2 = normalize(row.get("Буруу хариулт 2"))
        buruuh3 = normalize(row.get("Буруу хариулт 3"))

        if not task or not hicheel or not angi:
            continue

        if not correct_answer:
            correct_answer = "A"

        exists = Question.query.filter_by(angi=angi, hicheel=hicheel, asuult=task).first()
        if exists:
            continue

        q = Question(
            angi=angi,
            hicheel=hicheel,
            sedew=sedew,
            asuult=task,
            a_hariu=correct_answer,
            b_hariu=buruuh1,
            v_hariu=buruuh2,
            g_hariu=buruuh3,
            d_hariu="",
            image_url=image_url,
            zow_hariult=correct_answer[:1].upper(),
            tuwshin=2,
        )
        db.session.add(q)
        added += 1

    if added:
        db.session.commit()
    return added


def get_gspread_client():
    if not gspread:
        raise ImportError("gspread суулгагдаагүй байна. pip install gspread гэсэн командыг ашиглана уу.")

    if SERVICE_ACCOUNT_JSON:
        creds = json.loads(SERVICE_ACCOUNT_JSON)
        if hasattr(gspread, "service_account_from_dict"):
            return gspread.service_account_from_dict(creds)
        raise RuntimeError("gspread service_account_from_dict функц олдсонгүй")

    if os.path.exists(SERVICE_ACCOUNT_FILE):
        return gspread.service_account(filename=SERVICE_ACCOUNT_FILE)

    raise FileNotFoundError("Google service account файл олдсонгүй: " + SERVICE_ACCOUNT_FILE)


def append_test_result(suragch_ner, angi, hicheel, onoo, too):
    # Respect development mock flag to avoid writing to real Google Sheets.
    mock_flag = os.getenv("MOCK_GOOGLE_SHEETS", "false").lower() in ("1", "true", "yes")
    if mock_flag:
        # Avoid printing user-provided non-ASCII text to consoles that may not support it.
        print("MOCK: append skipped (MOCK_GOOGLE_SHEETS=true)")
        return

    client = get_gspread_client()
    sh = client.open_by_key(SHEET_ID)
    ws = sh.worksheet("Үр дүн")
    ws.append_row([
        suragch_ner,
        angi,
        hicheel,
        onoo,
        too,
        datetime.now().strftime("%Y-%m-%d %H:%M")
    ], value_input_option="RAW")


if __name__ == "__main__":
    try:
        added = import_sheet_questions()
        print(f"{added} асуулт импортлолоо")
    except Exception as exc:
        print("Sheet импортлох явцад алдаа гарлаа:", exc)
