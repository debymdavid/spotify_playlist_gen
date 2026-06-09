import logging
import spotipy
import config
from database import SpotifyDatabase
from utils import get_playlist_id_by_name

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def if_playlist_exists(sp, playlist_name):
    results = sp.current_user_playlists()
    return any(p['name'].lower() == playlist_name.lower() for p in results['items'])

def create_playlist(sp, user_id):
    try:
        db = SpotifyDatabase()
        playlist_songs = db.get_playlist_tracks(config.PLAYLIST_SIZE)

        if not playlist_songs:
            logger.error("No songs found to add to playlist")
            return None

        playlist_name = 'the better On Repeat'

        if if_playlist_exists(sp, playlist_name):
            playlist_id = get_playlist_id_by_name(sp, playlist_name)
            sp.playlist_replace_items(playlist_id, playlist_songs)
        else:
            sp.user_playlist_create(user=user_id, name=playlist_name, public=True)
            playlist_id = get_playlist_id_by_name(sp, playlist_name)
            sp.user_playlist_add_tracks(user_id, playlist_id, playlist_songs)

        print('_________ ADDED SONGS TO ON REPEAT PLAYLIST ______')

    except spotipy.SpotifyException as e:
        logger.error(f"Playlist creation failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return None