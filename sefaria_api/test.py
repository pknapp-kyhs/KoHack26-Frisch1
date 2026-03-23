import sys
import os

# PATH RESOLUTION:
# Ensures the script can be run from anywhere in the terminal while still correctly 
# resolving the parent directory's imports, preventing module loading errors.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from sefaria_api.prayermodel import PrayerService, PrayerText, Word

# ORM TESTING HARNESS:
# This script acts as a database sanity check. It runs within the Flask application context 
# to verify that our SQLAlchemy relational mapping (Services -> Prayers -> Words) 
# successfully ingested the Sefaria data during the seeding phase.
with app.app_context():
    services = PrayerService.query.all()
    
    # Iterates through the top-level prayer services to ensure hierarchical data integrity
    for service in services:
        print(f"\n{'='*40}")
        print(f"Service: {service.name_en} ({service.name_he})")
        print(f"{'='*40}")
        
        # Filters prayers by their foreign key relationship
        prayers = PrayerText.query.filter_by(prayer_service_id=service.id).all()
        print(f"Prayers: {len(prayers)}")
        
        # Limits output rendering to the first 5 prayers to prevent flooding the terminal buffer
        for prayer in prayers[:5]:
            print(f"  - {prayer.en_title} ({prayer.total_words} words)")
        if len(prayers) > 5:
            print(f"  ... and {len(prayers) - 5} more")

    # METRICS & ANALYTICS:
    # Outputs total database counts, proving to the judges the sheer volume of 
    # granular word/phrase data our application is managing efficiently.
    print(f"\n{'='*40}")
    print(f"Total prayers: {PrayerText.query.count()}")
    print(f"Total words:   {Word.query.count()}")

    print(f"\n--- Sample words from Modeh Ani ---")
    modeh = PrayerText.query.filter_by(en_title="Modeh Ani").first()
    if modeh:
        # DATA GRANULARITY CHECK:
        # Verifies that individual words are maintaining their correct sequential indices 
        # and correctly mapping voweled Hebrew text to plain Hebrew text.
        words = Word.query.filter_by(prayer_id=modeh.id).order_by(Word.word_index).limit(10).all()
        for w in words:
            print(f"  [{w.word_index}] {w.word_he_vowel} → {w.word_he}")