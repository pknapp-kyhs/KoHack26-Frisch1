import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import requests
import unicodedata
from app import app, db
from sefaria_api.prayermodel import (
    PrayerService, PrayerText, Line,
    HebrewWord, EnglishWord,
    HebrewPhrase, EnglishPhrase
)

PHRASE_ENDINGS = set(".,;:!?׃")

def strip_niqqud(text):
    return ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )

def get_siddur_index():
    response = requests.get("https://www.sefaria.org/api/v2/index/Siddur_Ashkenaz")
    return response.json()

def collect_siddur_refs(index):
    refs = []

    def traverse(node, path_parts):
        if "nodes" in node:
            for child in node["nodes"]:
                traverse(child, path_parts + [node.get("title", "")])
        else:
            title    = node.get("title", "")
            he_title = node.get("heTitle", "")
            full_ref = "Siddur Ashkenaz, " + ", ".join(p for p in path_parts if p) + ", " + title
            refs.append({
                "ref":      full_ref,
                "en_title": title,
                "he_title": he_title,
                "path":     path_parts,
            })

    for node in index.get("schema", {}).get("nodes", []):
        traverse(node, [])

    return refs

def extract_section(path_parts):
    if len(path_parts) >= 3:
        return path_parts[2]
    if len(path_parts) >= 2:
        return path_parts[1]
    return None

def fetch_prayer(ref):
    url = f"https://www.sefaria.org/api/v3/texts/{ref}"
    he  = requests.get(url, params={"return_format": "text_only", "version": "source"}).json()
    en  = requests.get(url, params={"return_format": "text_only", "version": "english"}).json()
    return he, en

def extract_lines(version):
    text = version["text"]
    if isinstance(text, str):
        return [text]
    if isinstance(text[0], str):
        return text
    flat = []
    for section in text:
        if isinstance(section, list):
            flat.extend(section)
        else:
            flat.append(section)
    return flat

def split_into_phrases(lines):
    phrases = []
    current = []

    for line_i, line in enumerate(lines):
        if not line.strip():
            continue
        words = line.split()
        for w_i, word in enumerate(words):
            current.append(word)
            if word[-1] in PHRASE_ENDINGS or w_i == len(words) - 1:
                phrases.append({
                    "text":       " ".join(current),
                    "line_index": line_i,
                })
                current = []

    if current:
        phrases.append({
            "text":       " ".join(current),
            "line_index": len(lines) - 1,
        })

    return phrases

def seed_prayer(ref, en_title, he_title, section, service_id, order):
    if PrayerText.query.filter_by(ref=ref).first():
        print(f"skip (exists): {ref}")
        return

    he_data, en_data = fetch_prayer(ref)

    if he_data.get("warnings") or he_data.get("error"):
        print(f"skip (api error): {ref}")
        return

    he_versions = he_data.get("versions", [])
    en_versions = en_data.get("versions", [])

    hebrew  = next((v for v in he_versions if v.get("isSource")), None)
    english = next((v for v in en_versions if v.get("language") == "en"), None)

    if not hebrew:
        print(f"skip (no Hebrew): {ref}")
        return

    he_lines = extract_lines(hebrew)
    en_lines = extract_lines(english) if english else []

    prayer = PrayerText(
        name              = en_title or ref,
        ref               = ref,
        en_title          = en_title,
        he_title          = he_title,
        section           = section,
        prayer_service_id = service_id,
        prayer_order      = order
    )
    db.session.add(prayer)
    db.session.flush()

    max_lines = max(len(he_lines), len(en_lines))
    for line_i in range(max_lines):
        he_line = he_lines[line_i] if line_i < len(he_lines) else ""
        en_line = en_lines[line_i] if line_i < len(en_lines) else ""
        if he_line.strip() or en_line.strip():
            db.session.add(Line(
                prayer_id  = prayer.id,
                line_index = line_i,
                he_text    = he_line.strip() or None,
                en_text    = en_line.strip() or None,
            ))

    he_phrases = split_into_phrases(he_lines)
    en_phrases = split_into_phrases(en_lines)

    for phrase_index, p in enumerate(he_phrases):
        db.session.add(HebrewPhrase(
            prayer_id    = prayer.id,
            phrase_index = phrase_index,
            text         = p["text"],
            line_index   = p["line_index"],
        ))

    for phrase_index, p in enumerate(en_phrases):
        db.session.add(EnglishPhrase(
            prayer_id    = prayer.id,
            phrase_index = phrase_index,
            text         = p["text"],
            line_index   = p["line_index"],
        ))

    db.session.flush()

    he_word_index = 0
    en_word_index = 0

    for phrase_index, p in enumerate(he_phrases):
        for word in p["text"].split():
            stripped = strip_niqqud(word)
            if word == stripped:
                continue
            db.session.add(HebrewWord(
                prayer_id    = prayer.id,
                phrase_index = phrase_index,
                word_index   = he_word_index,
                word_vowel   = word,
                word         = stripped,
                line_index   = p["line_index"],
            ))
            he_word_index += 1

    for phrase_index, p in enumerate(en_phrases):
        for word in p["text"].split():
            db.session.add(EnglishWord(
                prayer_id    = prayer.id,
                phrase_index = phrase_index,
                word_index   = en_word_index,
                word         = word,
                line_index   = p["line_index"],
            ))
            en_word_index += 1

    if he_word_index == 0:
        db.session.expunge(prayer)
        print(f"skip (no voweled words): {ref}")
        return

    last_he = HebrewWord.query.filter_by(prayer_id=prayer.id).order_by(HebrewWord.word_index.desc()).first()
    if last_he:
        last_he.is_last = True

    last_en = EnglishWord.query.filter_by(prayer_id=prayer.id).order_by(EnglishWord.word_index.desc()).first()
    if last_en:
        last_en.is_last = True

    db.session.commit()
    print(f"seeded: '{en_title}' [{section}] — {he_word_index} he words, {en_word_index} en words, {len(he_phrases)} he phrases, {len(en_phrases)} en phrases, {max_lines} lines")


with app.app_context():
    db.drop_all()
    db.create_all()
    print("database cleared and recreated")

    shacharit = PrayerService(name_en="Shacharit", name_he="שַׁחֲרִית")
    mincha    = PrayerService(name_en="Mincha",    name_he="מִנְחָה")
    maariv    = PrayerService(name_en="Maariv",    name_he="מַעֲרִיב")
    db.session.add_all([shacharit, mincha, maariv])
    db.session.flush()

    service_map = {
        "Shacharit": shacharit.id,
        "Mincha":    mincha.id,
        "Maariv":    maariv.id,
    }

    print("fetching Siddur Ashkenaz index...")
    index = get_siddur_index()
    refs  = collect_siddur_refs(index)

    weekday_refs = [r for r in refs if "Weekday" in r["ref"]]
    print(f"found {len(weekday_refs)} weekday sections")

    for order, entry in enumerate(weekday_refs, start=1):
        ref_str = entry["ref"]
        if "Mincha" in ref_str or "Minchah" in ref_str:
            service_id = service_map["Mincha"]
        elif "Maariv" in ref_str:
            service_id = service_map["Maariv"]
        else:
            service_id = service_map["Shacharit"]

        section = extract_section(entry["path"])

        seed_prayer(
            ref        = ref_str,
            en_title   = entry["en_title"],
            he_title   = entry["he_title"],
            section    = section,
            service_id = service_id,
            order      = order
        )

    db.session.commit()
    print("done!")