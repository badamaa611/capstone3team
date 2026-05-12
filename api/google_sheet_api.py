def undun_sheets_bichih(suragch_ner, hicheel, onoo, too):
    """Тест дууссан үед Google Sheets-т бичнэ"""
    gc = gspread.service_account(filename="service_account.json")
    sh = gc.open_by_key(SHEET_ID)
    ws = sh.worksheet("Үр дүн")
    ws.append_row([
        suragch_ner,
        hicheel, 
        onoo,
        too,
        datetime.now().strftime("%Y-%m-%d %H:%M")
    ])