# run this as: python migrate.py
from database import SpotifyDatabase

db = SpotifyDatabase()
imported = db.import_from_csv('track_log.csv')
print(f"Migrated {imported} tracks into SQLite.")