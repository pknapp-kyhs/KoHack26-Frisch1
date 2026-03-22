import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import requests
import unicodedata
from app import app, db
from sefaria_api.prayermodel import PrayerService, PrayerText, Word

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
            title = node.get("title", "")
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
    params = {"version": "source", "return_format": "text_only"}
    return requests.get(url, params=params).json()

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

def seed_prayer(ref, en_title, he_title, section, service_id, order):
    if PrayerText.query.filter_by(ref=ref).first():
        print(f"skip (exists): {ref}")
        return

    data = fetch_prayer(ref)

    if data.get("warnings") or data.get("error"):
        print(f"skip (api error): {ref}")
        return

    versions = data.get("versions", [])
    hebrew = next((v for v in versions if v.get("isSource")), None)

    if not hebrew:
        print(f"skip (no Hebrew): {ref}")
        return

    lines = extract_lines(hebrew)

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

    word_index = 0
    for line_i, line in enumerate(lines):
        if not line.strip():
            continue
        for word in line.split():
            stripped = strip_niqqud(word)
            if word == stripped:
                continue
            db.session.add(Word(
                prayer_id     = prayer.id,
                word_index    = word_index,
                word_he_vowel = word,
                word_he       = stripped,
                line_index    = line_i
            ))
            word_index += 1

    if word_index == 0:
        db.session.expunge(prayer)
        print(f"skip (no voweled words): {ref}")
        return

    prayer.total_words = word_index
    db.session.flush()

    last = Word.query.filter_by(
        prayer_id=prayer.id
    ).order_by(Word.word_index.desc()).first()
    if last:
        last.is_last = True

    db.session.commit()
    print(f"seeded: '{en_title}' [{section}] — {word_index} words")


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
    refs = collect_siddur_refs(index)

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