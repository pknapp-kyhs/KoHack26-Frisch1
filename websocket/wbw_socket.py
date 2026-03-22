from flask_socketio import emit
from extensions import socketio
from sefaria_api.prayermodel import PrayerService, PrayerText, Word


def _get_words(service_name, prayer_name, lang, section=None):
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

    words = (
        Word.query
        .filter_by(prayer_id=prayer.id)
        .order_by(Word.word_index)
        .all()
    )

    if lang == "vowel":
        return [w.word_he_vowel for w in words if w.word_he_vowel], None
    if lang == "he":
        return [w.word_he for w in words if w.word_he], None
    if lang == "en":
        return [w.word_en for w in words if w.word_en], None

    return None, f"Unknown lang '{lang}'."


@socketio.on("start_wbw")
def handle_start_wbw(data):
    service_name = data.get("service", "Shacharit")
    prayer_name  = data.get("prayer", "")
    lang         = data.get("lang", "vowel")
    wpm          = max(1, int(data.get("wpm", 60)))
    section      = data.get("section", None)

    words, error = _get_words(service_name, prayer_name, lang, section)

    if error:
        emit("wbw_error", {"message": error})
        return

    delay_ms = round((60 / wpm) * 1000)
    emit("wbw_ready", {"words": words, "delay_ms": delay_ms})
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