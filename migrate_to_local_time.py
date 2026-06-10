# migrate_to_local_time.py
# One-time script to convert existing UTC timestamps in the DB to Gulf Standard Time (UTC+4)
# Run once with: python3 migrate_to_local_time.py

import sqlite3
import shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path

DB_PATH = "spotify_data.db"
BACKUP_PATH = "spotify_data_pre_migration.db"
GST = timezone(timedelta(hours=4))


def migrate():
    # ── Step 1: Backup ────────────────────────────────────────────────────────
    shutil.copy2(DB_PATH, BACKUP_PATH)
    print(f"✅ Backup created at {BACKUP_PATH}")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # ── Step 2: Fetch all rows ────────────────────────────────────────────────
    cursor.execute("SELECT id, date_played, time_played FROM tracks")
    rows = cursor.fetchall()
    print(f"Found {len(rows)} tracks to migrate")

    # ── Step 3: Convert each row ──────────────────────────────────────────────
    updated = 0
    skipped = 0
    errors  = 0

    for row_id, date_played, time_played in rows:
        try:
            # Parse as UTC
            utc_dt = datetime.fromisoformat(f"{date_played}T{time_played}").replace(tzinfo=timezone.utc)

            # Convert to GST (UTC+4)
            gst_dt = utc_dt.astimezone(GST)

            new_date = gst_dt.strftime("%Y-%m-%d")
            new_time = gst_dt.strftime("%H:%M:%S")

            # Skip rows that are already the same (already local or no change)
            if new_date == date_played and new_time == time_played:
                skipped += 1
                continue

            cursor.execute(
                "UPDATE tracks SET date_played = ?, time_played = ? WHERE id = ?",
                (new_date, new_time, row_id)
            )
            updated += 1

        except Exception as e:
            if "UNIQUE constraint" in str(e):
                # Row already stored in local time — target timestamp already exists, skip it
                skipped += 1
            else:
                print(f"  ⚠️  Row {row_id} ({date_played} {time_played}): {e}")
                errors += 1

    conn.commit()
    conn.close()

    # ── Step 4: Summary ───────────────────────────────────────────────────────
    print(f"\nMigration complete:")
    print(f"  Updated : {updated}")
    print(f"  Skipped : {skipped} (already correct)")
    print(f"  Errors  : {errors}")
    print(f"\nYour original data is safely backed up at '{BACKUP_PATH}'")
    print("You can delete the backup once you've verified the dashboard looks correct.")


if __name__ == "__main__":
    if not Path(DB_PATH).exists():
        print(f"❌ Could not find {DB_PATH} — make sure you run this from your project folder")
    else:
        migrate()