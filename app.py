import csv
import os
import sqlite3

from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_login import login_required

from extensions import bcrypt, db, login_manager
from models import User


app = Flask(__name__)
app.config['SECRET_KEY'] = 'smart-brain-secret-key-2026'

basedir = os.path.abspath(os.path.dirname(__file__))
QUESTION_DB_PATH = os.path.join(basedir, 'capstone.db')
QUESTION_CSV_PATH = os.path.join(basedir, 'capstone data - Sheet1.csv')

if os.getenv("RENDER"):
    db_path = "/tmp/user.db"
else:
    db_path = os.path.join(basedir, 'instance', 'user.db')
    os.makedirs(os.path.join(basedir, 'instance'), exist_ok=True)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
bcrypt.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'auth.login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def _connect_question_db():
    con = sqlite3.connect(QUESTION_DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def _answer_key(raw_answer, options):
    answer_map = {
        'A': 'a',
        'B': 'b',
        'C': 'c',
        'V': 'c',
        'В': 'c',
        'D': 'd',
        'G': 'd',
        'Г': 'd',
    }
    raw = str(raw_answer or '').strip()
    answer = answer_map.get(raw.upper())
    if answer:
        return answer

    for key, value in options.items():
        if str(value).strip().lower() == raw.lower():
            return key
    return 'a'


def _question_from_db_row(row):
    options = {
        'a': row['a_hariu'] or '',
        'b': row['b_hariu'] or '',
        'c': row['v_hariu'] or '',
        'd': row['g_hariu'] or row['d_hariu'] or '',
    }
    keys = row.keys()
    return {
        'id': row['id'],
        'grade': str(row['angi']),
        'subject': row['hicheel'] or '',
        'topic': row['sedew'] or '',
        'q': row['asuult'] or '',
        'image': row['image_url'] if 'image_url' in keys else '',
        'a': options['a'],
        'b': options['b'],
        'c': options['c'],
        'd': options['d'],
        'answer': _answer_key(row['zow_hariult'], options),
    }


def _normalize_grade(value):
    raw = str(value or '').strip()
    if not raw:
        return ''
    try:
        number = float(raw)
        if number.is_integer():
            return str(int(number))
    except ValueError:
        pass
    return raw


def _normalize_subject(value):
    return ' '.join(str(value or '').strip().split())


def _row_has_any_value(row):
    return any(str(value or '').strip() for value in row.values())


def _question_from_csv_row(row, row_number):
    if not _row_has_any_value(row):
        return None

    question_text = str(row.get('Асуулт') or '').strip()
    grade = _normalize_grade(row.get('Анги'))
    subject = _normalize_subject(row.get('Хичээл'))
    correct_answer = str(row.get('зөв хариулт') or '').strip()

    if not question_text or not grade or not subject or not correct_answer:
        return None

    return {
        'id': f'csv-{row_number}',
        'grade': grade,
        'subject': subject,
        'topic': _normalize_subject(row.get('TEXT')) or subject,
        'q': question_text,
        'image': str(row.get('link') or '').strip(),
        'a': correct_answer,
        'b': str(row.get('Буруу хариулт 1') or '').strip(),
        'c': str(row.get('Буруу хариулт 2') or '').strip(),
        'd': str(row.get('Буруу хариулт 3') or '').strip(),
        'answer': 'a',
    }


def load_csv_questions():
    if not os.path.exists(QUESTION_CSV_PATH):
        return []

    questions = []
    with open(QUESTION_CSV_PATH, encoding='utf-8-sig', newline='') as f:
        for row_number, row in enumerate(csv.DictReader(f), start=1):
            question = _question_from_csv_row(row, row_number)
            if question:
                questions.append(question)
    return questions


def get_subjects_by_grade():
    subjects = {'5': [], '9': [], '12': []}

    for question in load_csv_questions():
        grade = question['grade']
        subject = question['subject']
        if grade in subjects and subject not in subjects[grade]:
            subjects[grade].append(subject)

    if any(subjects.values()):
        for grade in subjects:
            subjects[grade].sort()
        return subjects

    if os.path.exists(QUESTION_DB_PATH):
        with _connect_question_db() as con:
            rows = con.execute(
                "SELECT angi, hicheel FROM questions "
                "WHERE angi IS NOT NULL AND hicheel IS NOT NULL "
                "GROUP BY angi, hicheel ORDER BY hicheel"
            ).fetchall()
        for row in rows:
            grade = str(row['angi'])
            subject = _normalize_subject(row['hicheel'])
            if grade in subjects and subject not in subjects[grade]:
                subjects[grade].append(subject)

    for grade in subjects:
        subjects[grade].sort()
    return subjects


def get_first_subject(grade):
    subjects = get_subjects_by_grade().get(_normalize_grade(grade), [])
    return subjects[0] if subjects else None


def get_test_data(grade, subject):
    grade = _normalize_grade(grade)
    subject = _normalize_subject(subject)
    questions = [
        question for question in load_csv_questions()
        if question['grade'] == grade and question['subject'].lower() == subject.lower()
    ]

    if questions or not os.path.exists(QUESTION_DB_PATH):
        return questions

    if os.path.exists(QUESTION_DB_PATH):
        with _connect_question_db() as con:
            rows = con.execute(
                "SELECT * FROM questions "
                "WHERE angi = ? AND lower(trim(hicheel)) = lower(trim(?)) "
                "ORDER BY id LIMIT 10",
                (grade, subject),
            ).fetchall()
        questions = [_question_from_db_row(row) for row in rows]

    return questions


def _csv_questions_for_recommendations():
    return load_csv_questions()


def _shared_word_score(left, right):
    left_words = {word.lower() for word in str(left or '').split() if len(word) > 2}
    right_words = {word.lower() for word in str(right or '').split() if len(word) > 2}
    return len(left_words & right_words)


def get_similar_questions(wrong_questions, exclude_ids, limit=3):
    if not wrong_questions:
        return []

    grades = {str(q.get('grade')) for q in wrong_questions if q.get('grade')}
    subjects = {q.get('subject') for q in wrong_questions if q.get('subject')}
    topics = {q.get('topic') for q in wrong_questions if q.get('topic')}
    wrong_text = ' '.join(q.get('q', '') for q in wrong_questions)

    candidates = []

    if os.path.exists(QUESTION_DB_PATH):
        with _connect_question_db() as con:
            rows = con.execute("SELECT * FROM questions ORDER BY id").fetchall()
        for row in rows:
            if row['id'] in exclude_ids:
                continue
            question = _question_from_db_row(row)
            score = 0
            if question['grade'] in grades and question['subject'] in subjects and question['topic'] in topics:
                score += 8
            elif question['subject'] in subjects and question['topic'] in topics:
                score += 6
            elif question['grade'] in grades and question['subject'] in subjects:
                score += 5
            elif question['topic'] in topics:
                score += 3
            elif question['subject'] in subjects:
                score += 2
            elif question['grade'] in grades:
                score += 1
            score += min(_shared_word_score(wrong_text, question['q']), 2)
            if score:
                candidates.append((score, question))

    seen = {item[1]['id'] for item in candidates}
    for question in _csv_questions_for_recommendations():
        if question['id'] in seen or question['id'] in exclude_ids:
            continue
        score = 0
        if question['grade'] in grades and question['subject'] in subjects and question['topic'] in topics:
            score += 8
        elif question['subject'] in subjects and question['topic'] in topics:
            score += 6
        elif question['grade'] in grades and question['subject'] in subjects:
            score += 5
        elif question['topic'] in topics:
            score += 3
        elif question['subject'] in subjects:
            score += 2
        elif question['grade'] in grades:
            score += 1
        score += min(_shared_word_score(wrong_text, question['q']), 2)
        if score:
            candidates.append((score, question))
            seen.add(question['id'])

    candidates.sort(key=lambda item: (-item[0], str(item[1]['id'])))
    return [question for _, question in candidates[:limit]]


from auth import auth as auth_blueprint
app.register_blueprint(auth_blueprint, url_prefix='/auth')


@app.route('/')
def index():
    subjects = get_subjects_by_grade()
    return render_template(
        'index.html',
        subjects_5=subjects.get('5', []),
        subjects_9=subjects.get('9', []),
        subjects_12=subjects.get('12', []),
    )


@app.route('/tests')
def tests_page():
    return redirect(url_for('index'))


@app.route('/ai-chat')
@app.route('/ai-advisor')
def ai_advisor():
    return render_template('ai_advisor.html')


@app.route('/login')
def login_alias():
    return redirect(url_for('auth.login'))


@app.route('/register')
def register_alias():
    return redirect(url_for('auth.register'))


@app.route('/take-test/<grade>', methods=['GET'])
@app.route('/take-test/<grade>/<path:subject>', methods=['GET', 'POST'])
@login_required
def take_test(grade, subject=None):
    if not subject:
        subject = get_first_subject(grade)
        if not subject:
            flash('Энэ ангид асуулт олдсонгүй.', 'danger')
            return redirect(url_for('index'))
        return redirect(url_for('take_test', grade=grade, subject=subject))

    questions = get_test_data(grade, subject)
    if not questions:
        flash('Сонгосон анги, хичээлд асуулт олдсонгүй.', 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        correct_count = 0
        wrong_questions = []
        exclude_ids = set()

        for i, question in enumerate(questions):
            exclude_ids.add(question['id'])
            if request.form.get(f'q{i}') == question['answer']:
                correct_count += 1
            else:
                wrong_questions.append(question)

        similar_questions = get_similar_questions(wrong_questions, exclude_ids)
        session['test_result'] = {
            'niit_asuult': len(questions),
            'zow_too': correct_count,
            'buruu_too': len(questions) - correct_count,
            'score': f'{correct_count}/{len(questions)}',
            'grade': grade,
            'subject': subject,
            'ai_recommendation': 'Таны шалгалтын үр дүн тооцоологдлоо.',
            'similar_questions': similar_questions,
        }
        return redirect(url_for('test_result_page'))

    return render_template('test.html', grade=grade, subject=subject, questions=questions)


@app.route('/result')
@login_required
def test_result_page():
    result = session.get('test_result')
    if not result:
        return redirect(url_for('index'))
    return render_template('result.html', result=result)


with app.app_context():
    db.create_all()


if __name__ == '__main__':
    app.run(debug=True)
