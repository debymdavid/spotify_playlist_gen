import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

import track_logger
import find_repeat_songs
from UpdatePlaylist import UpdatePlaylist
from OrganizePlaylist import OrganizePlaylist
import create_on_repeat

def authenticate():
    try:

        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=os.getenv('SPOTIPY_CLIENT_ID'),
        client_secret=os.getenv('SPOTIPY_CLIENT_SECRET'),
        redirect_uri=os.getenv('SPOTIPY_REDIRECT_URI'),
        #scope='playlist-modify-public'
        scope='playlist-modify-public user-read-currently-playing user-read-playback-state user-read-recently-played'
        ))

        # Test the connection
        user_info = sp.current_user()
        if not user_info:
            raise Exception("Failed to get user info")

        return sp

    except spotipy.SpotifyException as e:
        logger.error(f"Spotify authentication failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        return None


def main():
    sp = authenticate()
    user_id = sp.current_user()["id"]

    #TrackLogger.create_header()
    track_logger.log_songs(sp)
    #TrackLogger.del_all_duplicates()
    print('Logging the tracks - done ✅')
    print()

    find_repeat_songs.create_file()
    find_repeat_songs.get_freq()
    print('Frequency of songs aquired ✅')

    create_on_repeat.create_playlist(sp,user_id)



if __name__ == '__main__':
    main()


#sp.user_playlist_create(user=user_id, name="Test Playlist", public=True)
'''
data = sp.current_user_playing_track()
track_id = data['item']['id']

sp.user_playlist_add_tracks(user_id,playlist_id,[track_id])

print("✅ Song added to playlist successfully!")

'''



