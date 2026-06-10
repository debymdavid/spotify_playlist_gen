import sqlite3
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

src = sqlite3.connect('spotify_data.db')
dst = psycopg2.connect(os.getenv('SUPABASE_DB_URL'))

rows = src.execute("SELECT date_played, time_played, track_id, track_name, artist_name FROM tracks").fetchall()
print(f"Migrating {len(rows)} tracks to Supabase...")

cur = dst.cursor()
cur.execute('''
    CREATE TABLE IF NOT EXISTS tracks (
        id SERIAL PRIMARY KEY,
        date_played DATE NOT NULL,
        time_played TIME NOT NULL,
        track_id TEXT NOT NULL,
        track_name TEXT NOT NULL,
        artist_name TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(date_played, time_played, track_id)
    )
''')

inserted = 0
for row in rows:
    try:
        cur.execute('''
            INSERT INTO tracks (date_played, time_played, track_id, track_name, artist_name)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
        ''', row)
        if cur.rowcount > 0:
            inserted += 1
    except Exception as e:
        print(f"  Skipped row: {e}")

dst.commit()
print(f"Done — {inserted} tracks migrated, {len(rows)-inserted} already existed or skipped")
src.close()
dst.close()