import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from sefaria_api.prayermodel import PrayerService, PrayerText, Word

def get_prayer_text(service_name, prayer_name, lang="vowel", section=None):
    with app.app_context():
        service = PrayerService.query.filter(
            PrayerService.name_en.ilike(service_name)
        ).first()

        if not service:
            raise ValueError(f"Service '{service_name}' not found.")

        query = PrayerText.query.filter(
            PrayerText.prayer_service_id == service.id,
            PrayerText.en_title.ilike(f"%{prayer_name}%")
        )

        if section:
            query = query.filter(PrayerText.section.ilike(f"%{section}%"))

        prayer = query.first()

        if not prayer:
            raise ValueError(f"Prayer '{prayer_name}' not found in {service_name}.")

        words = Word.query.filter_by(prayer_id=prayer.id).order_by(Word.word_index).all()

        if lang == "vowel":
            return " ".join(w.word_he_vowel for w in words)
        elif lang == "he":
            return " ".join(w.word_he for w in words)
        elif lang == "en":
            return " ".join(w.word_en for w in words if w.word_en)
        else:
            raise ValueError(f"Unknown lang '{lang}'. Use 'vowel', 'he', or 'en'.")