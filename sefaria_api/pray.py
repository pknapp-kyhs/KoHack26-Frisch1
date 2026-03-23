import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from sefaria_api.prayermodel import PrayerService, PrayerText, Word

# REUSABLE CLI COMPONENT:
# A generic, defensive-programming utility function that handles console user input.
# It traps invalid inputs in a loop until the user provides a valid integer choice, 
# preventing the application from crashing due to unexpected user behavior.
def pick_from_list(prompt, options, display_fn=str):
    print(f"\n{prompt}")
    for i, option in enumerate(options, start=1):
        print(f"  {i}. {display_fn(option)}")
    while True:
        choice = input("Enter number: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(options):
            return options[int(choice) - 1]
        print("Invalid choice, try again.")

# INTERACTIVE PRAYER LOGIC:
# This function powers the core word-by-word reading experience strictly via the terminal.
def run_prayer(prayer):
    # Enforces strict chronological ordering based on the word_index column
    words = Word.query.filter_by(prayer_id=prayer.id).order_by(Word.word_index).all()
    if not words:
        print("No words found for this prayer.")
        return

    # CLI UI/UX:
    # Provides a clean, organized header for the user, rendering both English and Right-To-Left Hebrew titles.
    print(f"\n{'='*50}")
    print(f"  {prayer.en_title}  |  {prayer.he_title[::-1]}")
    print(f"  {prayer.section}  |  {prayer.total_words} words")
    print(f"{'='*50}")
    print("Press ENTER to go word by word, or type 'q' to quit.\n")

    # PROGRESSIVE TEXT RENDERING:
    # Iterates through the database models one by one, waiting for user input before advancing.
    for word in words:
        # Reverses the Hebrew strings [::-1] purely for accurate terminal display, 
        # since standard consoles do not natively support RTL text rendering like web browsers do.
        display = word.word_he_vowel[::-1]
        plain = word.word_he[::-1]
        user_input = input(f"  {display}  ({plain})  > ").strip().lower()
        
        # Early exit condition
        if user_input == 'q':
            print("Exiting prayer.")
            return
            
        # State awareness: The database knows when the prayer block is finished
        if word.is_last:
            print("\nEnd of prayer.")
            return

def main():
    # Application context is required to query the database outside of a Flask route
    with app.app_context():
        while True:
            # 1. Fetch top-level services (Shacharit, Mincha, etc.)
            services = PrayerService.query.all()
            service = pick_from_list(
                "Which service?",
                services,
                display_fn=lambda s: f"{s.name_en} ({s.name_he})"
            )

            # 2. Dynamically extract unique sections nested inside the chosen service
            prayers = PrayerText.query.filter_by(prayer_service_id=service.id).all()
            sections = sorted(set(p.section for p in prayers if p.section))
            section = pick_from_list(
                "Which section?",
                sections,
                display_fn=str
            )

            # SEARCH ALGORITHM:
            # Uses a SQL ILIKE query (case-insensitive) to perform a wildcard search 
            # against the English titles within the specific service and section boundaries.
            query = input(f"\nSearch for a prayer in {section}: ").strip()
            results = PrayerText.query.filter(
                PrayerText.prayer_service_id == service.id,
                PrayerText.section == section,
                PrayerText.en_title.ilike(f"%{query}%")
            ).all()

            # Graceful error handling for failed searches
            if not results:
                print("No prayers found. Try again.")
                continue

            # 3. Present the filtered search results for final selection
            prayer = pick_from_list(
                "Which prayer?",
                results,
                display_fn=lambda p: f"{p.en_title}  |  {p.he_title}  ({p.total_words} words)"
            )

            # Dispatch the selected data to the interactive reader
            run_prayer(prayer)

            # Continuous execution loop allows users to read multiple prayers without restarting the script
            again = input("\nPray another? (y/n): ").strip().lower()
            if again != 'y':
                print("Shalom!")
                break

if __name__ == "__main__":
    main()