# Capstone Project — Шалгалтын Бэлтгэл Вэбсайт

## Тайлбар
5, 9, 12-р ангийн улсын шалгалтад бэлддэг адаптив тестийн платформ.

## Суурилуулах
```bash
pip install -r requirements.txt
cp .env.example .env   # .env файлдаа мэдээллээ бөглөнө
python database/seed.py
python app.py
```

## Бүтэц
```
capstone/
├── app.py              # Flask app үндсэн файл
├── config.py           # Тохиргоо
├── api/
│   ├── auth_routes.py  # Нэвтрэх / бүртгэх
│   ├── test_routes.py  # Тест үүсгэх, илгээх
│   └── ai_routes.py    # AI нэмэлт асуулт
├── database/
│   ├── schema.sql      # DB хүснэгтүүд
│   └── seed.py         # Жишээ өгөгдөл оруулах
├── templates/          # HTML хуудсууд
└── static/             # CSS, JS файлууд
```
