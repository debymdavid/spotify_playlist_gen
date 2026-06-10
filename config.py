import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Database — use Supabase URL if set, otherwise fall back to local SQLite
SUPABASE_DB_URL = os.getenv('SUPABASE_DB_URL')
DATABASE_PATH   = 'spotify_data.db'   # only used if Supabase URL is absent

# Database configuration
DATABASE_PATH = 'spotify_data.db'
BACKUP_DIR = 'backups'

# Create backup directory if it doesn't exist
Path(BACKUP_DIR).mkdir(exist_ok=True)

LIMIT_SONGS = 50
PLAYLIST_SIZE = 30