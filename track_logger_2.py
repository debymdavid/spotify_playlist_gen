# track_logger.py - Updated to use SQLite
from datetime import datetime
import logging
import spotipy
import requests
from database import SpotifyDatabase
import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SpotifyTrackLogger:
    def __init__(self, db_path: str = None):
        self.db = SpotifyDatabase(db_path)
    
    def get_recent_songs(self, sp) -> list:
        """Get recent songs from Spotify API"""
        try:
            all_tracks = []
            results = sp.current_user_recently_played(limit=config.LIMIT_SONGS)
            
            if not results or 'items' not in results:
                logger.warning("No recent tracks returned from API")
                return []
            
            for item in results['items']:
                track = item['track']
                played_at = item['played_at']
                played_dt = datetime.fromisoformat(played_at.replace("Z", "+00:00"))
                
                track_data = (
                    played_dt.date().isoformat(),      # date_played
                    played_dt.time().strftime("%H:%M:%S"),  # time_played
                    track['id'],                        # track_id
                    track['name'],                      # track_name
                    track['artists'][0]['name']         # artist_name
                )
                all_tracks.append(track_data)
            
            logger.info(f"Fetched {len(all_tracks)} tracks from Spotify API")
            return all_tracks
            
        except spotipy.SpotifyException as e:
            if e.http_status == 401:
                logger.error("Spotify authentication expired")
            elif e.http_status == 429:
                logger.error("Spotify API rate limit exceeded")
            elif e.http_status == 503:
                logger.error("Spotify service temporarily unavailable")
            else:
                logger.error(f"Spotify API error: {e}")
            return []
        except requests.exceptions.ConnectionError:
            logger.error("Network connection error")
            return []
        except requests.exceptions.Timeout:
            logger.error("Request timeout")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching songs: {e}")
            return []
    
    def log_songs(self, sp) -> bool:
        """Log recent songs to database"""
        try:
            tracks = self.get_recent_songs(sp)
            if not tracks:
                logger.info("No new tracks to log")
                return True
            
            inserted_count = self.db.add_tracks(tracks)
            
            if inserted_count > 0:
                logger.info(f"Successfully logged {inserted_count} new tracks")
            else:
                logger.info("No new tracks added (all were duplicates)")
            
            return True
            
        except Exception as e:
            logger.error(f"Error in log_songs: {e}")
            return False
    
    def get_statistics(self):
        """Get current database statistics"""
        return self.db.get_statistics()
    
    def print_statistics(self):
        """Print formatted statistics"""
        stats = self.get_statistics()
        
        print("\n=== Spotify Listening Statistics ===")
        print(f"Total plays: {stats.get('total_plays', 0)}")
        print(f"Unique tracks: {stats.get('unique_tracks', 0)}")
        print(f"Unique artists: {stats.get('unique_artists', 0)}")
        
        if stats.get('date_range'):
            start_date, end_date = stats['date_range']
            print(f"Date range: {start_date} to {end_date}")
        
        if stats.get('most_played_track'):
            track, artist, plays = stats['most_played_track']
            print(f"Most played track: '{track}' by {artist} ({plays} plays)")
        
        if stats.get('most_played_artist'):
            artist, plays = stats['most_played_artist']
            print(f"Most played artist: {artist} ({plays} plays)")
        
        print("=" * 40)

# Legacy functions for compatibility with your existing code
def log_songs(sp):
    """Compatibility function - use SpotifyTrackLogger.log_songs() instead"""
    logger = SpotifyTrackLogger()
    return logger.log_songs(sp)

def get_recent_songs(sp):
    """Compatibility function"""
    logger = SpotifyTrackLogger()
    return logger.get_recent_songs(sp)