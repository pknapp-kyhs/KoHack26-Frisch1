from flask_socketio import emit
from extensions import socketio
from sefaria_api.prayermodel import PrayerService, PrayerText, Line, HebrewWord, EnglishWord
import unicodedata


def strip_niqqud(text):
    return ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )


def clean_word(w):
    return strip_niqqud(w).strip(".,;:!?׃\"'")


def clean_word_en(w):
    return w.lower().strip(".,;:!?\"'")


def _get_service(service_name):
    return PrayerService.query.filter(
        PrayerService.name_en.ilike(service_name)
    ).first()


def score_match(query_words, db_words, start_idx):
    window    = len(query_words) * 2
    db_slice  = [clean_word(w.word) for w in db_words[start_idx:start_idx + window]]
    matched   = 0
    last_seen = -1

    for qw in query_words:
        for j in range(last_seen + 1, len(db_slice)):
            if db_slice[j] == qw or qw in db_slice[j] or db_slice[j] in qw:
                matched  += 1
                last_seen = j
                break

    return matched / len(query_words) if query_words else 0


def score_match_english(query_words, db_words_flat, start_idx):
    window    = len(query_words) * 2
    db_slice  = db_words_flat[start_idx:start_idx + window]
    matched   = 0
    last_seen = -1

    for qw in query_words:
        for j in range(last_seen + 1, len(db_slice)):
            if db_slice[j] == qw or qw in db_slice[j] or db_slice[j] in qw:
                matched  += 1
                last_seen = j
                break

    return matched / len(query_words) if query_words else 0


def find_all_matches(service, query_words, threshold=0.66):
    prayers = PrayerText.query.filter_by(
        prayer_service_id=service.id
    ).order_by(PrayerText.prayer_order).all()

    matches = []

    for prayer in prayers:
        db_words = HebrewWord.query.filter_by(
            prayer_id=prayer.id
        ).order_by(HebrewWord.word_index).all()

        if not db_words:
            continue

        seen_lines = set()
        for i in range(len(db_words)):
            score = score_match(query_words, db_words, i)
            if score >= threshold:
                line_index = db_words[i].line_index
                if line_index not in seen_lines:
                    seen_lines.add(line_index)
                    matches.append({
                        "prayer_id":   prayer.id,
                        "prayer_name": prayer.en_title,
                        "line_index":  line_index,
                        "score":       round(score, 2),
                    })

    return matches


def find_all_matches_english(service, query_words, threshold=0.66):
    prayers = PrayerText.query.filter_by(
        prayer_service_id=service.id
    ).order_by(PrayerText.prayer_order).all()

    matches = []

    for prayer in prayers:
        db_words = EnglishWord.query.filter_by(
            prayer_id=prayer.id
        ).order_by(EnglishWord.word_index).all()

        if not db_words:
            continue

        db_words_flat = [clean_word_en(w.word) for w in db_words if w.word]

        seen_lines = set()
        for i in range(len(db_words)):
            score = score_match_english(query_words, db_words_flat, i)
            if score >= threshold:
                line_index = db_words[i].line_index
                if line_index not in seen_lines:
                    seen_lines.add(line_index)
                    matches.append({
                        "prayer_id":   prayer.id,
                        "prayer_name": prayer.en_title,
                        "line_index":  line_index,
                        "score":       round(score, 2),
                    })

    return matches


@socketio.on("highlight_search")
def handle_highlight_search(data):
    service_name = data.get("service", "Shacharit")
    phrase       = data.get("word", "").strip()
    display_lang = data.get("display_lang", "he")
    search_lang  = data.get("search_lang", "he")

    if not phrase:
        return

    service = _get_service(service_name)
    if not service:
        emit("highlight_error", {"message": f"Service '{service_name}' not found."})
        return

    if search_lang == "en":
        query_words = [clean_word_en(w) for w in phrase.split() if clean_word_en(w)]
        if not query_words:
            emit("highlight_miss", {"word": phrase})
            return
        matches = find_all_matches_english(service, query_words)
    else:
        query_words = [clean_word(w) for w in phrase.split() if clean_word(w)]
        if not query_words:
            emit("highlight_miss", {"word": phrase})
            return
        matches = find_all_matches(service, query_words)

    if not matches:
        emit("highlight_miss", {"word": phrase, "score": 0})
        return

    emit("highlight_results", {
        "word":         phrase,
        "display_lang": display_lang,
        "matches":      matches,
    })


@socketio.on("highlight_goto")
def handle_highlight_goto(data):
    prayer_id    = data.get("prayer_id")
    line_index   = data.get("line_index")
    display_lang = data.get("display_lang", "he")

    prayer = PrayerText.query.get(prayer_id)
    if not prayer:
        emit("highlight_error", {"message": "Prayer not found."})
        return

    lines = Line.query.filter_by(
        prayer_id=prayer.id
    ).order_by(Line.line_index).all()

    emit("highlight_found", {
        "line_index":  line_index,
        "prayer_name": prayer.en_title,
        "display_lang": display_lang,
        "lines": [
            {
                "line_index": l.line_index,
                "he_text":    l.he_text,
                "en_text":    l.en_text,
            }
            for l in lines
        ]
    })