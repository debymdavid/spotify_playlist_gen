# create_on_repeat.py - Updated to use SQLite
import spotipy
import logging
from database import SpotifyDatabase
import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OnRepeatPlaylistCreator:
    def __init__(self, db_path: str = None):
        self.db = SpotifyDatabase(db_path)
    
    def if_playlist_exists(self, sp, playlist_name: str) -> bool:
        """Check if playlist exists for current user"""
        try:
            all_playlists = []
            results = sp.current_user_playlists()
            
            for playlist in results['items']:
                all_playlists.append(playlist['name'].lower())
            
            return playlist_name.lower() in all_playlists
            
        except Exception as e:
            logger.error(f"Error checking playlist existence: {e}")
            return False
    
    def get_playlist_id_by_name(self, sp, playlist_name: str) -> str:
        """Get playlist ID by name"""
        try:
            results = sp.current_user_playlists()
            
            for playlist in results['items']:
                if playlist['name'].lower() == playlist_name.lower():
                    return playlist['id']
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting playlist ID: {e}")
            return None
    
    def create_playlist(self, sp, user_id: str, playlist_name: str = None) -> bool:
        """Create or update the On Repeat playlist"""
        try:
            if not playlist_name:
                playlist_name = 'the better On Repeat'
            
            # Get songs for playlist from database
            playlist_songs = self.db.get_playlist_tracks(config.PLAYLIST_SIZE)
            
            if not playlist_songs:
                logger.error("No songs available for playlist creation")
                return False
            
            logger.info(f"Creating playlist with {len(playlist_songs)} songs")
            
            # Create or update playlist
            if self.if_playlist_exists(sp, playlist_name):
                playlist_id = self.get_playlist_id_by_name(sp, playlist_name)
                if playlist_id:
                    sp.playlist_replace_items(playlist_id, playlist_songs)
                    logger.info(f"Updated existing playlist '{playlist_name}'")
                else:
                    logger.error("Could not find existing playlist ID")
                    return False
            else:
                # Create new playlist
                new_playlist = sp.user_playlist_create(
                    user=user_id, 
                    name=playlist_name, 
                    public=True,
                    description="Automatically generated based on your most played tracks"
                )
                playlist_id = new_playlist['id']
                sp.user_playlist_add_tracks(user_id, playlist_id, playlist_songs)
                logger.info(f"Created new playlist '{playlist_name}'")
            
            print('_________ ADDED SONGS TO ON REPEAT PLAYLIST ______')
            return True
            
        except spotipy.SpotifyException as e:
            if e.http_status == 403:
                logger.error("Insufficient permissions to create playlist")
            else:
                logger.error(f"Playlist creation failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error creating playlist: {e}")
            return False
    
    def preview_playlist(self) -> list:
        """Preview what songs would be in the playlist"""
        try:
            track_frequencies = self.db.get_track_frequencies(config.PLAYLIST_SIZE)
            
            print(f"\n=== Playlist Preview ({len(track_frequencies)} songs) ===")
            for i, (track_id, track_name, artist_name, frequency) in enumerate(track_frequencies, 1):
                print(f"{i:2d}. {track_name} by {artist_name} ({frequency} plays)")
            print("=" * 50)
            
            return [row[0] for row in track_frequencies]  # Return track IDs
            
        except Exception as e:
            logger.error(f"Error previewing playlist: {e}")
            return []

# Legacy function for compatibility
def create_playlist(sp, user_id: str):
    """Compatibility function - use OnRepeatPlaylistCreator.create_playlist() instead"""
    creator = OnRepeatPlaylistCreator()
    return creator.create_playlist(sp, user_id)