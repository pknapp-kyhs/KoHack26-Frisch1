from extensions import db

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
    lines             = db.relationship("Line", backref="prayer_text",
                            order_by="Line.line_index")
    hebrew_words      = db.relationship("HebrewWord", backref="prayer_text",
                            order_by="HebrewWord.word_index")
    english_words     = db.relationship("EnglishWord", backref="prayer_text",
                            order_by="EnglishWord.word_index")
    hebrew_phrases    = db.relationship("HebrewPhrase", backref="prayer_text",
                            order_by="HebrewPhrase.phrase_index")
    english_phrases   = db.relationship("EnglishPhrase", backref="prayer_text",
                            order_by="EnglishPhrase.phrase_index")

class Line(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    prayer_id  = db.Column(db.Integer, db.ForeignKey("prayer_text.id"), nullable=False)
    line_index = db.Column(db.Integer, nullable=False, index=True)
    he_text    = db.Column(db.String())
    en_text    = db.Column(db.String())

class HebrewWord(db.Model):
    id            = db.Column(db.Integer, primary_key=True)
    prayer_id     = db.Column(db.Integer, db.ForeignKey("prayer_text.id"), nullable=False)
    phrase_index  = db.Column(db.Integer)
    word_index    = db.Column(db.Integer, nullable=False, index=True)
    word_vowel    = db.Column(db.String())
    word          = db.Column(db.String(), index=True)
    line_index    = db.Column(db.Integer)
    is_last       = db.Column(db.Boolean, default=False)

class EnglishWord(db.Model):
    id            = db.Column(db.Integer, primary_key=True)
    prayer_id     = db.Column(db.Integer, db.ForeignKey("prayer_text.id"), nullable=False)
    phrase_index  = db.Column(db.Integer)
    word_index    = db.Column(db.Integer, nullable=False, index=True)
    word          = db.Column(db.String(), index=True)
    line_index    = db.Column(db.Integer)
    is_last       = db.Column(db.Boolean, default=False)

class HebrewPhrase(db.Model):
    id           = db.Column(db.Integer, primary_key=True)
    prayer_id    = db.Column(db.Integer, db.ForeignKey("prayer_text.id"), nullable=False)
    phrase_index = db.Column(db.Integer, nullable=False)
    text         = db.Column(db.String(), nullable=False)
    line_index   = db.Column(db.Integer)

class EnglishPhrase(db.Model):
    id           = db.Column(db.Integer, primary_key=True)
    prayer_id    = db.Column(db.Integer, db.ForeignKey("prayer_text.id"), nullable=False)
    phrase_index = db.Column(db.Integer, nullable=False)
    text         = db.Column(db.String(), nullable=False)
    line_index   = db.Column(db.Integer)