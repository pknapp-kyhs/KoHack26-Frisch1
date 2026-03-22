import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from sefaria_api.prayermodel import PrayerService, PrayerText, Word

with app.app_context():
    services = PrayerService.query.all()
    for service in services:
        print(f"\n{'='*40}")
        print(f"Service: {service.name_en} ({service.name_he})")
        print(f"{'='*40}")
        prayers = PrayerText.query.filter_by(prayer_service_id=service.id).all()
        print(f"Prayers: {len(prayers)}")
        for prayer in prayers[:5]:
            print(f"  - {prayer.en_title} ({prayer.total_words} words)")
        if len(prayers) > 5:
            print(f"  ... and {len(prayers) - 5} more")

    print(f"\n{'='*40}")
    print(f"Total prayers: {PrayerText.query.count()}")
    print(f"Total words:   {Word.query.count()}")

    print(f"\n--- Sample words from Modeh Ani ---")
    modeh = PrayerText.query.filter_by(en_title="Modeh Ani").first()
    if modeh:
        words = Word.query.filter_by(prayer_id=modeh.id).order_by(Word.word_index).limit(10).all()
        for w in words:
            print(f"  [{w.word_index}] {w.word_he_vowel} → {w.word_he}")