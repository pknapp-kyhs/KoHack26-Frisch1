import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from sefaria_api.prayermodel import PrayerService, PrayerText, Word

PHRASE_ENDINGS = set(".,;:!?׃")


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


def _word_text(word: Word, lang: str) -> str:
    if lang == "vowel":
        return word.word_he_vowel or ""
    if lang == "he":
        return word.word_he or ""
    if lang == "en":
        return word.word_en or ""
    raise ValueError(f"Unknown lang '{lang}'. Use 'vowel', 'he', or 'en'.")


def get_prayer_text(service_name, prayer_name, lang="vowel", section=None):
    with app.app_context():
        prayer = _get_prayer(service_name, prayer_name, section)
        words = Word.query.filter_by(prayer_id=prayer.id).order_by(Word.word_index).all()

        if lang == "en":
            return " ".join(w.word_en for w in words if w.word_en)
        return " ".join(_word_text(w, lang) for w in words)


def get_prayer_words(service_name, prayer_name, lang="vowel", section=None):
    with app.app_context():
        prayer = _get_prayer(service_name, prayer_name, section)
        words = (
            Word.query
            .filter_by(prayer_id=prayer.id)
            .order_by(Word.word_index)
            .all()
        )
        return [_word_text(w, lang) for w in words if _word_text(w, lang).strip()]


def get_prayer_phrases(service_name, prayer_name, lang="vowel", section=None):
    with app.app_context():
        prayer = _get_prayer(service_name, prayer_name, section)
        words = (
            Word.query
            .filter_by(prayer_id=prayer.id)
            .order_by(Word.word_index)
            .all()
        )

        phrases = []
        current = []

        for w in words:
            text = _word_text(w, lang)

            if text.strip():
                current.append(text)

            if text and text[-1] in PHRASE_ENDINGS:
                if current:
                    phrases.append(" ".join(current))
                    current = []

        if current:
            phrases.append(" ".join(current))

        return phrases