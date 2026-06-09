import logging
import spotipy
import requests
import config
from database import SpotifyDatabase
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_recent_songs(sp):
    try:
        all_tracks = []
        results = sp.current_user_recently_played(limit=config.LIMIT_SONGS)
        if not results or 'items' not in results:
            logger.warning("No recent tracks returned from API")
            return []

        for item in results['items']:
            track = item['track']
            played_dt = datetime.fromisoformat(item['played_at'].replace("Z", "+00:00"))
            all_tracks.append((
                played_dt.date().isoformat(),
                played_dt.time().strftime("%H:%M:%S"),
                track['id'],
                track['name'],
                track['artists'][0]['name']
            ))
        return all_tracks

    except spotipy.SpotifyException as e:
        logger.error(f"Spotify API error: {e}")
        return []
    except requests.exceptions.ConnectionError:
        logger.error("Network connection error")
        return []
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return []

def log_songs(sp):
    tracks = get_recent_songs(sp)
    if not tracks:
        return False
    db = SpotifyDatabase()
    inserted = db.add_tracks(tracks)
    logger.info(f"Logged {inserted} new tracks (duplicates automatically skipped)")
    return True