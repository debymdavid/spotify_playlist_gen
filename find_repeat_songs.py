import logging
import config
from database import SpotifyDatabase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_freq():
    db = SpotifyDatabase()
    return db.get_track_frequencies()

def get_artist_freq():
    db = SpotifyDatabase()
    return db.get_artist_frequencies()