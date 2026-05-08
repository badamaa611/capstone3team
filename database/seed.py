"""
seed.py — Жишээ өгөгдөл болон Excel-ээс асуулт оруулах скрипт
Ашиглах:
  python database/seed.py           # Жишээ асуулт
  python database/seed.py excel asuultiin_san_zagvar.xlsx
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app, db, bcrypt
from models import User, Question

def seed_demo_users(app):
    with app.app_context():
        if not User.query.filter_by(email="bagsh@test.mn").first():
            db.session.add(User(
                ner="Тестийн Багш", email="bagsh@test.mn",
                nuuts_ug=bcrypt.generate_password_hash("bagsh123").decode("utf-8"),
                duwer="bagsh"
            ))
        if not User.query.filter_by(email="suragch@test.mn").first():
            db.session.add(User(
                ner="Тестийн Сурагч", email="suragch@test.mn",
                nuuts_ug=bcrypt.generate_password_hash("suragch123").decode("utf-8"),
                duwer="suragch", angi="12"
            ))
        db.session.commit()
        print("Хэрэглэгчид нэмэгдлээ")
        print("  Багш:   bagsh@test.mn / bagsh123")
        print("  Сурагч: suragch@test.mn / suragch123")

def seed_demo_questions(app):
    with app.app_context():
        if Question.query.count() > 0:
            print(f"Асуулт аль хэдийн байна ({Question.query.count()} ширхэг)")
            return
        qs = [
            Question(angi="12", hicheel="Биологи", sedew="Амьсгал ба хийн солилцоо",
                blueprint_kod="БИ-2.1",
                asuult="Аэроб амьсгалын үед гликолиз эсийн аль хэсэгт явагддаг вэ?",
                a_hariu="Митохондри", b_hariu="Цитоплазм",
                v_hariu="Хлоропласт", g_hariu="Бөөм",
                zow_hariult="B", tuwshin=1),
            Question(angi="12", hicheel="Биологи", sedew="Дархлаа ба өвчний тухай ойлголт",
                blueprint_kod="БИ-3.2",
                asuult="Вакцины бустер тун хийлгэхэд эсрэг биеийн хэмжээ огцом ихсэх шалтгаан нь юу вэ?",
                a_hariu="Вакцинд нян үржсэн тул",
                b_hariu="Санах ойн эсүүд эрчимтэй ажилласан тул",
                v_hariu="Цусны улаан эс олшрсон тул",
                g_hariu="Лейкоцит хэлбэр өөрчлөгдсөн тул",
                zow_hariult="B", tuwshin=2),
            Question(angi="9", hicheel="Математик", sedew="Квадрат тэгшитгэл",
                blueprint_kod="МА-2.1",
                asuult="x2-5x+6=0 тэгшитгэлийн шийдийг ол.",
                a_hariu="x=1, x=6", b_hariu="x=2, x=3",
                v_hariu="x=-2, x=-3", g_hariu="x=5, x=1",
                zow_hariult="B", tuwshin=2),
            Question(angi="5", hicheel="Монгол хэл", sedew="Үгийн бүтэц",
                blueprint_kod="МХ-1.1",
                asuult="Сургууль үгийн язгуур хэсгийг ол.",
                a_hariu="Сур", b_hariu="Сург",
                v_hariu="Сургуул", g_hariu="Сурагч",
                zow_hariult="A", tuwshin=1),
        ]
        db.session.add_all(qs)
        db.session.commit()
        print(f"{len(qs)} жишээ асуулт нэмэгдлээ")

def seed_from_excel(app, filepath):
    try:
        import openpyxl
    except ImportError:
        print("pip install openpyxl --break-system-packages")
        return
    wb = openpyxl.load_workbook(filepath)
    ws = wb.active
    with app.app_context():
        added = 0
        for row in ws.iter_rows(min_row=5, values_only=True):
            if not row[5]:
                continue
            db.session.add(Question(
                angi=str(row[1] or ""), hicheel=str(row[2] or ""),
                sedew=str(row[3] or ""), blueprint_kod=str(row[4] or ""),
                asuult=str(row[5]),
                a_hariu=str(row[6] or ""), b_hariu=str(row[7] or ""),
                v_hariu=str(row[8] or ""), g_hariu=str(row[9] or ""),
                d_hariu=str(row[10] or ""),
                zow_hariult=str(row[11] or "A"),
                tuwshin=int(row[12] or 1),
            ))
            added += 1
        db.session.commit()
        print(f"Excel-ээс {added} асуулт нэмэгдлээ")

if __name__ == "__main__":
    app = create_app()
    seed_demo_users(app)
    if len(sys.argv) > 1 and sys.argv[1] == "excel":
        fp = sys.argv[2] if len(sys.argv) > 2 else "asuultiin_san_zagvar.xlsx"
        seed_from_excel(app, fp)
    else:
        seed_demo_questions(app)
    print("\nДууслаа! Одоо: python app.py")
    print("Браузер: http://127.0.0.1:5000")
