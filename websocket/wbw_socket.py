from flask_socketio import emit
from extensions import socketio
from sefaria_api.prayermodel import PrayerService, PrayerText, HebrewWord, EnglishWord, HebrewPhrase, EnglishPhrase


def _get_prayer(service_name, prayer_name, section=None):
    service = PrayerService.query.filter(
        PrayerService.name_en.ilike(service_name)
    ).first()
    if not service:
        return None, f"Service '{service_name}' not found."

    query = PrayerText.query.filter(
        PrayerText.prayer_service_id == service.id,
        PrayerText.en_title.ilike(f"%{prayer_name}%"),
    )
    if section:
        query = query.filter(PrayerText.section.ilike(f"%{section}%"))

    prayer = query.first()
    if not prayer:
        return None, f"Prayer '{prayer_name}' not found."

    return prayer, None


def _get_words(prayer, lang):
    if lang == "vowel":
        words = HebrewWord.query.filter_by(prayer_id=prayer.id).order_by(HebrewWord.word_index).all()
        return [w.word_vowel for w in words if w.word_vowel]
    if lang == "he":
        words = HebrewWord.query.filter_by(prayer_id=prayer.id).order_by(HebrewWord.word_index).all()
        return [w.word for w in words if w.word]
    if lang == "en":
        words = EnglishWord.query.filter_by(prayer_id=prayer.id).order_by(EnglishWord.word_index).all()
        return [w.word for w in words if w.word]
    return []


def _get_phrases(prayer, lang):
    if lang in ("vowel", "he"):
        phrases = HebrewPhrase.query.filter_by(prayer_id=prayer.id).order_by(HebrewPhrase.phrase_index).all()
        return [p.text for p in phrases]
    if lang == "en":
        phrases = EnglishPhrase.query.filter_by(prayer_id=prayer.id).order_by(EnglishPhrase.phrase_index).all()
        return [p.text for p in phrases]
    return []


@socketio.on("start_wbw")
def handle_start_wbw(data):
    service_name = data.get("service", "Shacharit")
    prayer_name  = data.get("prayer", "")
    lang         = data.get("lang", "vowel")
    wpm          = max(1, int(data.get("wpm", 60)))
    section      = data.get("section", None)

    prayer, error = _get_prayer(service_name, prayer_name, section)
    if error:
        emit("wbw_error", {"message": error})
        return

    words   = _get_words(prayer, lang)
    phrases = _get_phrases(prayer, lang)

    delay_ms = round((60 / wpm) * 1000)
    emit("wbw_ready", {
        "words":    words,
        "phrases":  phrases,
        "delay_ms": delay_ms,
    })
    emit("wbw_done", {})


@socketio.on("get_prayers")
def handle_get_prayers(data):
    service_name = data.get("service", "Shacharit")
    service = PrayerService.query.filter(
        PrayerService.name_en.ilike(service_name)
    ).first()

    if not service:
        emit("prayers_list", {"prayers": []})
        return

    prayers = [
        {"id": p.id, "en_title": p.en_title, "he_title": p.he_title}
        for p in service.prayer_texts
        if p.en_title
    ]
    emit("prayers_list", {"prayers": prayers})