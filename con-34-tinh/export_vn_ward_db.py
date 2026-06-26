import json
import sqlite3
import unicodedata
from pathlib import Path

WARD_JSON = "all-ward.json"
DB_FILE = "vn_ward.db"


def to_text(value):
    if value is None:
        return ""

    if isinstance(value, dict):
        for key in ["local", "vi", "name", "full_name", "short_name", "value", "en", "slug", "id"]:
            if key in value and value[key] not in (None, ""):
                return to_text(value[key])

        return " ".join(to_text(v) for v in value.values() if v not in (None, ""))

    if isinstance(value, list):
        return " ".join(to_text(v) for v in value if v not in (None, ""))

    return str(value)


def normalize_text(text):
    text = to_text(text).lower().strip()
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = text.replace("đ", "d")
    return " ".join(text.split())


def pick(obj, keys, default=""):
    if not isinstance(obj, dict):
        return default

    for key in keys:
        if key in obj and obj[key] not in (None, ""):
            return to_text(obj[key])

    return default


def load_json_list(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        data = json.load(f)

    if isinstance(data, list):
        return data

    for key in ["data", "items", "wards", "communes", "features"]:
        if key in data and isinstance(data[key], list):
            return data[key]

    raise ValueError(f"Không nhận diện được cấu trúc JSON: {path}")


def get_lat_lon(obj):
    lat = pick(obj, ["lat", "latitude"])
    lon = pick(obj, ["lon", "lng", "longitude"])

    geo = obj.get("geo")
    if isinstance(geo, dict):
        lat = lat or pick(geo, ["lat", "latitude"])
        lon = lon or pick(geo, ["lon", "lng", "longitude"])

    coords = obj.get("coordinates")
    if isinstance(coords, dict):
        lat = lat or pick(coords, ["lat", "latitude"])
        lon = lon or pick(coords, ["lon", "lng", "longitude"])

    center = obj.get("center")
    if isinstance(center, dict):
        lat = lat or pick(center, ["lat", "latitude"])
        lon = lon or pick(center, ["lon", "lng", "longitude"])

    try:
        lat = float(lat) if lat not in ("", None) else None
    except ValueError:
        lat = None

    try:
        lon = float(lon) if lon not in ("", None) else None
    except ValueError:
        lon = None

    return lat, lon


def main():
    if not Path(WARD_JSON).exists():
        print(f"Missing file: {WARD_JSON}")
        return

    if Path(DB_FILE).exists():
        print(f"DB already exists: {DB_FILE}")
        print("Xóa vn_ward.db trước nếu muốn build lại.")
        return

    wards = load_json_list(WARD_JSON)

    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE wards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ward_code TEXT,
            ward_name TEXT,
            ward_name_en TEXT,
            ward_slug TEXT,
            level INTEGER,
            level_name TEXT,
            province_code TEXT,
            province_name TEXT,
            province_name_en TEXT,
            province_slug TEXT,
            lat REAL,
            lon REAL,
            search_text TEXT
        )
    """)

    insert_rows = []

    for w in wards:
        name_obj = w.get("name", {})
        parent = w.get("parent", {})
        parent_name_obj = parent.get("name", {}) if isinstance(parent, dict) else {}

        code_obj = w.get("code", {})

        ward_code = pick(w, ["id"])
        if not ward_code and isinstance(code_obj, dict):
            ward_code = pick(code_obj, ["id", "code"])

        ward_name = ""
        ward_name_en = ""
        ward_slug = ""

        if isinstance(name_obj, dict):
            ward_name = pick(name_obj, ["local", "vi", "name"])
            ward_name_en = pick(name_obj, ["en", "english"])
            ward_slug = pick(name_obj, ["slug"])
        else:
            ward_name = pick(w, ["name"])
            ward_name_en = pick(w, ["name_en"])
            ward_slug = ""

        level = pick(w, ["level"])

        level_name_obj = w.get("level_name", {})
        if isinstance(level_name_obj, dict):
            level_name = pick(level_name_obj, ["local", "vi", "name"])
        else:
            level_name = to_text(level_name_obj)

        province_code = ""
        province_name = ""
        province_name_en = ""
        province_slug = ""

        if isinstance(parent, dict):
            province_code = pick(parent, ["id", "code"])

            if isinstance(parent_name_obj, dict):
                province_name = pick(parent_name_obj, ["local", "vi", "name"])
                province_name_en = pick(parent_name_obj, ["en", "english"])
                province_slug = pick(parent_name_obj, ["slug"])
            else:
                province_name = to_text(parent_name_obj)

        lat, lon = get_lat_lon(w)

        search_text = normalize_text(" ".join([
            ward_code,
            ward_name,
            ward_name_en,
            ward_slug,
            level_name,
            province_code,
            province_name,
            province_name_en,
            province_slug,
        ]))

        insert_rows.append((
            ward_code,
            ward_name,
            ward_name_en,
            ward_slug,
            int(level) if str(level).isdigit() else None,
            level_name,
            province_code,
            province_name,
            province_name_en,
            province_slug,
            lat,
            lon,
            search_text
        ))

    cur.executemany("""
        INSERT INTO wards (
            ward_code,
            ward_name,
            ward_name_en,
            ward_slug,
            level,
            level_name,
            province_code,
            province_name,
            province_name_en,
            province_slug,
            lat,
            lon,
            search_text
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, insert_rows)

    cur.execute("CREATE INDEX idx_wards_code ON wards(ward_code)")
    cur.execute("CREATE INDEX idx_wards_name ON wards(ward_name)")
    cur.execute("CREATE INDEX idx_wards_province_code ON wards(province_code)")
    cur.execute("CREATE INDEX idx_wards_province_name ON wards(province_name)")
    cur.execute("CREATE INDEX idx_wards_search ON wards(search_text)")
    cur.execute("CREATE INDEX idx_wards_lat_lon ON wards(lat, lon)")

    conn.commit()
    conn.close()

    print(f"Done: {DB_FILE}")
    print(f"Imported wards: {len(insert_rows):,}")


if __name__ == "__main__":
    main()