from app import db

class PrayerService(db.Model):
    id           = db.Column(db.Integer, primary_key=True)
    name_en      = db.Column(db.String(), nullable=False)
    name_he      = db.Column(db.String())
    prayer_texts = db.relationship("PrayerText", backref="prayer_service",
                       order_by="PrayerText.prayer_order")

class PrayerText(db.Model):
    id                = db.Column(db.Integer, primary_key=True)
    name              = db.Column(db.String(), nullable=False)
    ref               = db.Column(db.String(), nullable=False)
    prayer_service_id = db.Column(db.Integer, db.ForeignKey("prayer_service.id"))
    prayer_order      = db.Column(db.Integer)
    section           = db.Column(db.String())
    en_title          = db.Column(db.String())
    he_title          = db.Column(db.String())
    total_words       = db.Column(db.Integer)
    words             = db.relationship("Word", backref="prayer_text",
                            order_by="Word.word_index")

class Word(db.Model):
    id            = db.Column(db.Integer, primary_key=True)
    prayer_id     = db.Column(db.Integer, db.ForeignKey("prayer_text.id"), nullable=False)
    word_index    = db.Column(db.Integer, nullable=False, index=True)
    word_en       = db.Column(db.String(), index=True)
    word_he_vowel = db.Column(db.String())
    word_he       = db.Column(db.String(), index=True)
    line_index    = db.Column(db.Integer)
    is_last       = db.Column(db.Boolean, default=False)