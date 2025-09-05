import csv 
import os 
from datetime import datetime
import logging
import spotipy
import requests
import config
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_header():
    track_log = open(config.TRACK_LOG_FILE,'w',newline = '')
    pen = csv.writer(track_log)
    pen.writerow(['Date','Time','Track ID','Track Name','Artist Name'])
    track_log.close()

def get_recent_songs(sp):
    try:
        all_tracks = [] 
        results = sp.current_user_recently_played(limit=config.LIMIT_SONGS)

        if not results or 'items' not in results:
            logger.warning("No recent tracks returned from API")
            return []
        
        for idx, item in enumerate(results['items'], start=1):

            track = item['track']
            played_at = item['played_at']
            played_dt = datetime.fromisoformat(played_at.replace("Z", "+00:00"))

            track_id = track['id']
            track_name = track['name']
            artist_name = track['artists'][0]['name']
            date_played = played_dt.date().isoformat()
            time_played = played_dt.time().strftime("%H:%M:%S")

            track_data = [date_played,time_played,track_id,track_name,artist_name]
            all_tracks.append(track_data)

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

def log_songs(sp):
    try:
        all_tracks = get_recent_songs(sp)
        track_log = open(config.TRACK_LOG_FILE,'r')
        new_track_log = open('new Track Log','w',newline ='')
        pen = csv.writer(new_track_log)
        eye = csv.reader(track_log)
        
        for row in eye:
            if row in all_tracks:
                all_tracks.remove(row)
            pen.writerow(row)
        pen.writerows(all_tracks)
        track_log.close()
        new_track_log.close()
        os.remove(config.TRACK_LOG_FILE)
        os.rename('New Track Log',config.TRACK_LOG_FILE)
    
    except FileNotFoundError:
        logger.error("Track Log file not found")
        return False
    except PermissionError:
        logger.error("Permission denied accessing files")
        return False
    except OSError as e:
        logger.error(f"File system error: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error in log_songs: {e}")
        # Clean up temp file if it exists
        if os.path.exists('new Track Log'):
            os.remove('new Track Log')
        return False
    
def del_all_duplicates():
    track_log = open(config.TRACK_LOG_FILE,'r')
    updated_log = []
    eye = csv.reader(track_log)
    for row in eye:
        if row not in updated_log:
            updated_log.append(row)
    track_log.close()

    track_log = open(config.TRACK_LOG_FILE,'w',newline='')
    pen = csv.writer(track_log)
    pen.writerows(updated_log)
    track_log.close()


