# models.py — Database хүснэгтүүд (SQLAlchemy ORM)
from extensions import db
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    __tablename__ = "user"
    id       = db.Column(db.Integer, primary_key=True)
    ner      = db.Column(db.String(150), nullable=False)
    email    = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)

    def __repr__(self):
        return f"<User {self.ner}>"


class Question(db.Model):
    __tablename__ = "questions"
    id            = db.Column(db.Integer, primary_key=True)
    angi          = db.Column(db.String(5), nullable=False)   # '5','9','12'
    hicheel       = db.Column(db.String(50), nullable=False)
    sedew         = db.Column(db.String(200), nullable=False)
    blueprint_kod = db.Column(db.String(20))
    asuult        = db.Column(db.Text, nullable=False)
    a_hariu       = db.Column(db.Text)
    b_hariu       = db.Column(db.Text)
    v_hariu       = db.Column(db.Text)
    g_hariu       = db.Column(db.Text)
    d_hariu       = db.Column(db.Text)
    zow_hariult   = db.Column(db.String(1), nullable=False) 
    image_url     = db.Column(db.String(500), nullable=True)  # Зургаар асуулт оруулахад зориулав
    tuwshin       = db.Column(db.SmallInteger, nullable=False) # 1/2/3
    created       = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "angi": self.angi,
            "hicheel": self.hicheel,
            "sedew": self.sedew,
            "blueprint_kod": self.blueprint_kod,
            "asuult": self.asuult,
            "a_hariu": self.a_hariu,
            "b_hariu": self.b_hariu,
            "v_hariu": self.v_hariu,
            "g_hariu": self.g_hariu,
            "d_hariu": self.d_hariu,
            "zow_hariult": self.zow_hariult,
            "tuwshin": self.tuwshin,
            "image_url": self.image_url,
            "created": self.created.isoformat() if self.created else None
        }


class TestSession(db.Model):
    __tablename__ = "test_sessions"
    id            = db.Column(db.Integer, primary_key=True)
    suragch_id    = db.Column(db.Integer, db.ForeignKey("user.id"))
    angi          = db.Column(db.String(5))
    hicheel       = db.Column(db.String(50))
    egneliin_tsag = db.Column(db.DateTime, default=datetime.utcnow)
    duusah_tsag   = db.Column(db.DateTime)
    niit_onoo     = db.Column(db.Integer, default=0)
    too           = db.Column(db.Integer, default=0)

    answers = db.relationship("TestAnswer", backref="session", lazy=True)


class TestAnswer(db.Model):
    __tablename__ = "test_answers"
    id            = db.Column(db.Integer, primary_key=True)
    session_id    = db.Column(db.Integer, db.ForeignKey("test_sessions.id"))
    question_id   = db.Column(db.Integer, db.ForeignKey("questions.id"))
    ogson_hariult = db.Column(db.String(1))
    zuw_esehuu    = db.Column(db.Boolean)
    ai_asuu       = db.Column(db.Boolean, default=False)


class WeakTopic(db.Model):
    __tablename__ = "weak_topics"
    id         = db.Column(db.Integer, primary_key=True)
    suragch_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    hicheel    = db.Column(db.String(50))
    sedew      = db.Column(db.String(200))
    aldaa_too  = db.Column(db.Integer, default=1)
    updated    = db.Column(db.DateTime, default=datetime.utcnow)
