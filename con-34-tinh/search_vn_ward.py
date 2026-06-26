import sqlite3
import unicodedata

DB_FILE = "vn_ward.db"


def normalize_text(text):
    text = str(text or "").lower().strip()
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = text.replace("đ", "d")
    return " ".join(text.split())


def search_ward(keyword, province_keyword=None, limit=30):
    keyword_norm = normalize_text(keyword)
    province_norm = normalize_text(province_keyword)

    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    where = []
    params = []

    if keyword_norm:
        where.append("search_text LIKE ?")
        params.append(f"%{keyword_norm}%")

    if province_norm:
        where.append("search_text LIKE ?")
        params.append(f"%{province_norm}%")

    if not where:
        where.append("1 = 1")

    params.append(limit)

    sql = f"""
        SELECT
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
            lon
        FROM wards
        WHERE {" AND ".join(where)}
        ORDER BY province_name, ward_name
        LIMIT ?
    """

    rows = cur.execute(sql, params).fetchall()
    conn.close()

    return [dict(row) for row in rows]


def print_results(rows):
    if not rows:
        print("No results.")
        return

    for r in rows:
        print("-" * 70)
        print("Ward Code   :", r["ward_code"])
        print("Ward        :", r["ward_name"])
        print("Ward EN     :", r["ward_name_en"])
        print("Level       :", r["level"], "-", r["level_name"])
        print("Province    :", r["province_name"])
        print("Province EN :", r["province_name_en"])
        print("Lat/Lon     :", r["lat"], r["lon"])


def main():
    print("Search VN wards/communes")
    print()

    while True:
        keyword = input("Ward keyword, empty to exit: ").strip()

        if not keyword:
            break

        province = input("Province keyword, empty = all: ").strip()

        rows = search_ward(keyword, province_keyword=province or None)
        print_results(rows)
        print()


if __name__ == "__main__":
    main()