import sys
import os

# PATH RESOLUTION:
# Ensures the script can be run from anywhere in the terminal while still correctly 
# resolving the parent directory's imports, preventing module loading errors.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from extensions import db
from sefaria_api.prayermodel import PrayerService, PrayerText, HebrewWord, EnglishWord, HebrewPhrase, EnglishPhrase


# INTERNAL HELPER FUNCTION:
# The leading underscore denotes this is a "private" function meant only for internal use 
# within this module. It handles the heavy lifting of resolving human-readable names 
# into explicit Database ORM objects via highly forgiving SQL ILIKE queries.
def _get_prayer(service_name, prayer_name, section=None):
    # DYNAMIC SEARCHING:
    # Uses case-insensitive querying (.ilike) so the API doesn't crash if a user 
    # types "shacharit" instead of "Shacharit".
    service = PrayerService.query.filter(
        PrayerService.name_en.ilike(service_name)
    ).first()
    
    # DEFENSIVE PROGRAMMING: 
    # Explicitly trapping edge cases and raising informative ValueErrors 
    # prevents silent failures downstream in the application stack.
    if not service:
        raise ValueError(f"Service '{service_name}' not found.")

    # COMPOSITE FILTERING:
    # We chain SQLAlchemy filters together to drill down through our relational schema 
    # (Service -> Section -> Prayer). Wildcard formatting (%) allows partial matches.
    query = PrayerText.query.filter(
        PrayerText.prayer_service_id == service.id,
        PrayerText.en_title.ilike(f"%{prayer_name}%"),
    )
    if section:
        query = query.filter(PrayerText.section.ilike(f"%{section}%"))

    prayer = query.first()
    if not prayer:
        raise ValueError(f"Prayer '{prayer_name}' not found in {service_name}.")

    return prayer


# DATA ACCESS LAYER (DAL) METHODS:
# These functions act as an API for the rest of the backend. They completely abstract 
# away the complex SQLAlchemy logic, allowing other developers (or routes) to simply ask 
# for "words" and receive a clean list of strings.

def get_hebrew_words(service_name, prayer_name, section=None, voweled=True):
    # CONTEXT MANAGEMENT:
    # We explicitly wrap these queries in the Flask app_context to ensure they can be 
    # called safely from background tasks, WebSockets, or CLI scripts outside of normal web requests.
    with app.app_context():
        prayer = _get_prayer(service_name, prayer_name, section)
        
        # Chronological ordering ensures the text is always returned in readable sequence
        words = HebrewWord.query.filter_by(prayer_id=prayer.id).order_by(HebrewWord.word_index).all()
        
        # CONDITIONAL DATA EXTRACTION:
        # Dynamically returns either the raw, stripped string (for search) 
        # or the voweled string (for display) based on the boolean flag.
        if voweled:
            return [w.word_vowel for w in words if w.word_vowel]
        return [w.word for w in words if w.word]


def get_english_words(service_name, prayer_name, section=None):
    with app.app_context():
        prayer = _get_prayer(service_name, prayer_name, section)
        words = EnglishWord.query.filter_by(prayer_id=prayer.id).order_by(EnglishWord.word_index).all()
        return [w.word for w in words if w.word]


def get_hebrew_phrases(service_name, prayer_name, section=None):
    with app.app_context():
        prayer = _get_prayer(service_name, prayer_name, section)
        # Pulls the "chunked" text strings rather than individual words, 
        # supporting the Phrase-by-Phrase reading mode in the frontend.
        phrases = HebrewPhrase.query.filter_by(prayer_id=prayer.id).order_by(HebrewPhrase.phrase_index).all()
        return [p.text for p in phrases]


def get_english_phrases(service_name, prayer_name, section=None):
    with app.app_context():
        prayer = _get_prayer(service_name, prayer_name, section)
        phrases = EnglishPhrase.query.filter_by(prayer_id=prayer.id).order_by(EnglishPhrase.phrase_index).all()
        return [p.text for p in phrases]