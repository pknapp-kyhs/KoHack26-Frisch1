from extensions import db

# DATA ARCHITECTURE: MACRO LEVEL
# This is the top-level entity in our relational hierarchy. It represents an entire 
# prayer service (e.g., Shacharit, Mincha). We use a One-to-Many relationship to 
# connect a single service to hundreds of individual prayer components.
class PrayerService(db.Model):
    id           = db.Column(db.Integer, primary_key=True)
    name_en      = db.Column(db.String(), nullable=False)
    name_he      = db.Column(db.String())
    
    # RELATIONAL MAPPING:
    # We dynamically link the child PrayerText records back to this service. 
    # 'order_by' ensures that whenever we query a service, the backend automatically 
    # returns the prayers in strict chronological order without needing complex SQL ordering.
    prayer_texts = db.relationship("PrayerText", backref="prayer_service",
                       order_by="PrayerText.prayer_order")

# DATA ARCHITECTURE: MESO LEVEL
# This model acts as the central hub for a specific prayer block. 
# It is highly relational, connecting downwards into parallel data streams 
# (Lines, Words, and Phrases) for both English and Hebrew.
class PrayerText(db.Model):
    id                = db.Column(db.Integer, primary_key=True)
    name              = db.Column(db.String(), nullable=False)
    ref               = db.Column(db.String(), nullable=False)
    prayer_service_id = db.Column(db.Integer, db.ForeignKey("prayer_service.id"))
    prayer_order      = db.Column(db.Integer)
    section           = db.Column(db.String())
    en_title          = db.Column(db.String())
    he_title          = db.Column(db.String())
    
    # CASCADING RELATIONSHIPS:
    # By separating Lines, Words, and Phrases, we allow the frontend UI to instantly 
    # toggle between different reading modes (Word-by-Word, Phrase-by-Phrase, or Line-by-Line)
    # just by asking the database for a different relationship array.
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

# PARALLEL ALIGNMENT MODEL:
# The Line model solves the complex i18n (Internationalization) problem of 
# displaying Left-to-Right English and Right-to-Left Hebrew side-by-side. 
# By storing them in the same row, they are perfectly synchronized.
class Line(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    prayer_id  = db.Column(db.Integer, db.ForeignKey("prayer_text.id"), nullable=False)
    # PERFORMANCE OPTIMIZATION: 
    # We index 'line_index' because the WebSocket Chazzan feature frequently queries 
    # specific lines in real-time. Indexing changes query time from O(N) to O(log N).
    line_index = db.Column(db.Integer, nullable=False, index=True)
    he_text    = db.Column(db.String())
    en_text    = db.Column(db.String())

# MICRO-DATA TOKENIZATION: HEBREW
# Breaking texts down to the absolute granular word level. 
# This powers the automated reading UI and advanced search algorithms.
class HebrewWord(db.Model):
    id            = db.Column(db.Integer, primary_key=True)
    prayer_id     = db.Column(db.Integer, db.ForeignKey("prayer_text.id"), nullable=False)
    phrase_index  = db.Column(db.Integer)
    word_index    = db.Column(db.Integer, nullable=False, index=True)
    
    # DATA NORMALIZATION:
    # 'word_vowel' stores the visually rich Hebrew text (with Niqqud).
    # 'word' stores the plain, stripped text. We index 'word' to allow 
    # blazing-fast, forgiving search capabilities for users typing on standard keyboards.
    word_vowel    = db.Column(db.String())
    word          = db.Column(db.String(), index=True)
    
    line_index    = db.Column(db.Integer)
    
    # STATE BOUNDARY TRACKING:
    # A lightweight boolean flag that allows our frontend reading loop to know 
    # exactly when it has reached the end of a prayer section.
    is_last       = db.Column(db.Boolean, default=False)

# MICRO-DATA TOKENIZATION: ENGLISH
# Maps English translation words. Syncs up with the Hebrew word tokenization 
# structure to allow future 1-to-1 tooltip dictionary translations.
class EnglishWord(db.Model):
    id            = db.Column(db.Integer, primary_key=True)
    prayer_id     = db.Column(db.Integer, db.ForeignKey("prayer_text.id"), nullable=False)
    phrase_index  = db.Column(db.Integer)
    word_index    = db.Column(db.Integer, nullable=False, index=True)
    word          = db.Column(db.String(), index=True)
    line_index    = db.Column(db.Integer)
    is_last       = db.Column(db.Boolean, default=False)

# CHUNKED READING MODELS:
# Phrases act as the intermediate structural layer between a full 'Line' and a granular 'Word'.
# They allow for natural, grammatically correct "chunked" reading modes in the UI.
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