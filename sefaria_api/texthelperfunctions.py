import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from extensions import db
from sefaria_api.prayermodel import PrayerService, PrayerText, HebrewWord, EnglishWord, HebrewPhrase, EnglishPhrase


def _get_prayer(service_name, prayer_name, section=None):
    service = PrayerService.query.filter(
        PrayerService.name_en.ilike(service_name)
    ).first()
    if not service:
        raise ValueError(f"Service '{service_name}' not found.")

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


def get_hebrew_words(service_name, prayer_name, section=None, voweled=True):
    with app.app_context():
        prayer = _get_prayer(service_name, prayer_name, section)
        words = HebrewWord.query.filter_by(prayer_id=prayer.id).order_by(HebrewWord.word_index).all()
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
        phrases = HebrewPhrase.query.filter_by(prayer_id=prayer.id).order_by(HebrewPhrase.phrase_index).all()
        return [p.text for p in phrases]


def get_english_phrases(service_name, prayer_name, section=None):
    with app.app_context():
        prayer = _get_prayer(service_name, prayer_name, section)
        phrases = EnglishPhrase.query.filter_by(prayer_id=prayer.id).order_by(EnglishPhrase.phrase_index).all()
        return [p.text for p in phrases]