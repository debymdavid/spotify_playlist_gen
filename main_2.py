# main.py - Updated to use SQLite
import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import logging
from pathlib import Path

# Import your updated modules
from track_logger import SpotifyTrackLogger
from create_on_repeat import OnRepeatPlaylistCreator
from database import SpotifyDatabase
import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

def authenticate():
    """Authenticate with Spotify API"""
    try:
        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=os.getenv('SPOTIPY_CLIENT_ID'),
            client_secret=os.getenv('SPOTIPY_CLIENT_SECRET'),
            redirect_uri=os.getenv('SPOTIPY_REDIRECT_URI'),
            scope='playlist-modify-public user-read-currently-playing user-read-playback-state user-read-recently-played'
        ))
        
        # Test the connection
        user_info = sp.current_user()
        if not user_info:
            raise Exception("Failed to get user info")
        
        logger.info(f"Authenticated as: {user_info.get('display_name', user_info['id'])}")
        return sp
        
    except spotipy.SpotifyException as e:
        logger.error(f"Spotify authentication failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        return None

def migrate_csv_data():
    """One-time migration from CSV files to SQLite (if CSV files exist)"""
    csv_path = Path(config.TRACK_LOG_FILE)
    
    if csv_path.exists():
        print("Found existing CSV data. Migrating to SQLite...")
        db = SpotifyDatabase()
        imported_count = db.import_from_csv(str(csv_path))
        
        if imported_count > 0:
            print(f"✅ Migrated {imported_count} tracks from CSV to SQLite")
            
            # Create backup of CSV file
            backup_csv = csv_path.with_suffix('.csv.backup')
            csv_path.rename(backup_csv)
            print(f"✅ Original CSV backed up to {backup_csv}")
        else:
            print("❌ Failed to migrate CSV data")
    else:
        print("No existing CSV data found - starting fresh with SQLite")

def main():
    """Main application logic"""
    print("=== Spotify Track Logger with SQLite ===\n")
    
    # Authenticate with Spotify
    sp = authenticate()
    if not sp:
        print("❌ Authentication failed. Please check your Spotify credentials.")
        return
    
    user_id = sp.current_user()["id"]
    
    # One-time CSV migration (if needed)
    migrate_csv_data()
    
    # Initialize components
    track_logger = SpotifyTrackLogger()
    playlist_creator = OnRepeatPlaylistCreator()
    
    # Log recent tracks
    print("Fetching and logging recent tracks...")
    success = track_logger.log_songs(sp)
    
    if success:
        print('✅ Logging tracks completed')
        
        # Show statistics
        track_logger.print_statistics()
        
        # Preview playlist
        print("\nGenerating playlist preview...")
        playlist_creator.preview_playlist()
        
        # Create/update playlist
        print(f"\nCreating 'On Repeat' playlist with {config.PLAYLIST_SIZE} songs...")
        playlist_success = playlist_creator.create_playlist(sp, user_id)
        
        if playlist_success:
            print('✅ Playlist creation completed')
        else:
            print('❌ Playlist creation failed')
    else:
        print('❌ Track logging failed')

def interactive_mode():
    """Interactive mode for exploring your data"""
    print("\n=== Interactive Mode ===")
    db = SpotifyDatabase()
    
    while True:
        print("\nOptions:")
        print("1. Show statistics")
        print("2. Show top tracks")
        print("3. Show top artists")
        print("4. Backup database")
        print("5. Cleanup old data")
        print("6. Exit")
        
        choice = input("\nEnter choice (1-6): ").strip()
        
        if choice == '1':
            stats = db.get_statistics()
            print(f"\nTotal plays: {stats.get('total_plays', 0)}")
            print(f"Unique tracks: {stats.get('unique_tracks', 0)}")
            print(f"Unique artists: {stats.get('unique_artists', 0)}")
            if stats.get('most_played_track'):
                track, artist, plays = stats['most_played_track']
                print(f"Most played: '{track}' by {artist} ({plays} plays)")
        
        elif choice == '2':
            limit = int(input("How many top tracks to show? (default 10): ") or 10)
            tracks = db.get_track_frequencies(limit)
            print(f"\nTop {len(tracks)} tracks:")
            for i, (track_id, track_name, artist_name, freq) in enumerate(tracks, 1):
                print(f"{i:2d}. {track_name} by {artist_name} ({freq} plays)")
        
        elif choice == '3':
            artists = db.get_artist_frequencies()
            print(f"\nTop {min(10, len(artists))} artists:")
            for i, (artist_name, freq) in enumerate(artists[:10], 1):
                print(f"{i:2d}. {artist_name} ({freq} plays)")
        
        elif choice == '4':
            backup_path = db.backup_database()
            if backup_path:
                print(f"✅ Database backed up to: {backup_path}")
            else:
                print("❌ Backup failed")
        
        elif choice == '5':
            days = int(input("Keep data from how many days ago? (default 90): ") or 90)
            deleted = db.cleanup_old_data(days)
            print(f"✅ Deleted {deleted} old records")
        
        elif choice == '6':
            break
        
        else:
            print("Invalid choice")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--interactive':
        interactive_mode()
    else:
        main()