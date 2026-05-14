import csv
import sys
sys.path.insert(0, '.')

from app import create_app, db
from models import Question

app = create_app()

with app.app_context():
    # Өмнөх асуултуудыг устгах
    Question.query.delete()
    db.session.commit()
    print("Өмнөх асуултууд устгагдлаа")

    with open('questions.csv', 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        print("Баганууд:", reader.fieldnames)
        added = 0
        for row in reader:
            if not row.get('task'):
                continue
            q = Question(
                angi=str(row.get('Аль анги вэ?', '12')),
                hicheel=row.get('Хичээл', ''),
                sedew=row.get('Хичээл', ''),
                asuult=row.get('task', ''),
                a_hariu=row.get('зөв хариулт', ''),
                b_hariu=row.get('Буруу хариулт 1', ''),
                v_hariu=row.get('Буруу хариулт 2', ''),
                g_hariu=row.get('Буруу хариулт 3', ''),
                zow_hariult='A',
                tuwshin=2,
                image_url=row.get('link', ''),
            )
            db.session.add(q)
            added += 1
        db.session.commit()
        print(f'✅ {added} асуулт оруулсан!')