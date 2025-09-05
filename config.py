import os
from pathlib import Path

# Database configuration
DATABASE_PATH = 'spotify_data.db'
BACKUP_DIR = 'backups'

# Create backup directory if it doesn't exist
Path(BACKUP_DIR).mkdir(exist_ok=True)

LIMIT_SONGS = 50
TRACK_LOG_FILE = 'track_log.csv'
FREQ_LOG_FILE = 'freq_log.csv'
ARTIST_LOG_FILE = 'artist_log.csv'
PLAYLIST_SIZE = 30