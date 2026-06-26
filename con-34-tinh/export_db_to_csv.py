import csv
import sqlite3
from pathlib import Path

DB_FILE = "vn_ward.db"
CSV_FILE = "vn_ward.csv"

def main():
    if not Path(DB_FILE).exists():
        print(f"Missing DB file: {DB_FILE}")
        return

    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    rows = cur.execute("""
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
        ORDER BY province_name, ward_name
    """).fetchall()

    with open(CSV_FILE, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)

        writer.writerow([
            "ward_code",
            "ward_name",
            "ward_name_en",
            "ward_slug",
            "level",
            "level_name",
            "province_code",
            "province_name",
            "province_name_en",
            "province_slug",
            "lat",
            "lon"
        ])

        for row in rows:
            writer.writerow([
                row["ward_code"],
                row["ward_name"],
                row["ward_name_en"],
                row["ward_slug"],
                row["level"],
                row["level_name"],
                row["province_code"],
                row["province_name"],
                row["province_name_en"],
                row["province_slug"],
                row["lat"],
                row["lon"],
            ])

    conn.close()

    print(f"Done: {CSV_FILE}")
    print(f"Exported rows: {len(rows):,}")

if __name__ == "__main__":
    main()