import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from sefaria_api.prayermodel import PrayerService, PrayerText, Word

def pick_from_list(prompt, options, display_fn=str):
    print(f"\n{prompt}")
    for i, option in enumerate(options, start=1):
        print(f"  {i}. {display_fn(option)}")
    while True:
        choice = input("Enter number: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(options):
            return options[int(choice) - 1]
        print("Invalid choice, try again.")

def run_prayer(prayer):
    words = Word.query.filter_by(prayer_id=prayer.id).order_by(Word.word_index).all()
    if not words:
        print("No words found for this prayer.")
        return

    print(f"\n{'='*50}")
    print(f"  {prayer.en_title}  |  {prayer.he_title[::-1]}")
    print(f"  {prayer.section}  |  {prayer.total_words} words")
    print(f"{'='*50}")
    print("Press ENTER to go word by word, or type 'q' to quit.\n")

    for word in words:
        display = word.word_he_vowel[::-1]
        plain = word.word_he[::-1]
        user_input = input(f"  {display}  ({plain})  > ").strip().lower()
        if user_input == 'q':
            print("Exiting prayer.")
            return
        if word.is_last:
            print("\nEnd of prayer.")
            return

def main():
    with app.app_context():
        while True:
            services = PrayerService.query.all()
            service = pick_from_list(
                "Which service?",
                services,
                display_fn=lambda s: f"{s.name_en} ({s.name_he})"
            )

            prayers = PrayerText.query.filter_by(prayer_service_id=service.id).all()
            sections = sorted(set(p.section for p in prayers if p.section))
            section = pick_from_list(
                "Which section?",
                sections,
                display_fn=str
            )

            query = input(f"\nSearch for a prayer in {section}: ").strip()
            results = PrayerText.query.filter(
                PrayerText.prayer_service_id == service.id,
                PrayerText.section == section,
                PrayerText.en_title.ilike(f"%{query}%")
            ).all()

            if not results:
                print("No prayers found. Try again.")
                continue

            prayer = pick_from_list(
                "Which prayer?",
                results,
                display_fn=lambda p: f"{p.en_title}  |  {p.he_title}  ({p.total_words} words)"
            )

            run_prayer(prayer)

            again = input("\nPray another? (y/n): ").strip().lower()
            if again != 'y':
                print("Shalom!")
                break

if __name__ == "__main__":
    main()