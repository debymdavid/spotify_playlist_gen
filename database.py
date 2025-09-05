# database.py - Main database handler
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import List, Tuple, Optional, Dict
from pathlib import Path
import shutil
import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SpotifyDatabase:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or config.DATABASE_PATH
        self.init_database()
    
    def get_connection(self):
        """Get database connection with optimized settings"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
        conn.execute("PRAGMA journal_mode = WAL")  # Better concurrency
        return conn
    
    def init_database(self):
        """Initialize database with tables and indexes"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create main tracks table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tracks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date_played DATE NOT NULL,
                    time_played TIME NOT NULL,
                    track_id TEXT NOT NULL,
                    track_name TEXT NOT NULL,
                    artist_name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(date_played, time_played, track_id)
                )
            ''')
            
            # Create artists table for normalization (optional but recommended)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS artists (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    artist_name TEXT UNIQUE NOT NULL,
                    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_plays INTEGER DEFAULT 0
                )
            ''')
            
            # Create indexes for faster queries
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_track_id ON tracks(track_id)",
                "CREATE INDEX IF NOT EXISTS idx_artist_name ON tracks(artist_name)",
                "CREATE INDEX IF NOT EXISTS idx_date_played ON tracks(date_played)",
                "CREATE INDEX IF NOT EXISTS idx_track_artist ON tracks(track_name, artist_name)",
                "CREATE INDEX IF NOT EXISTS idx_created_at ON tracks(created_at)"
            ]
            
            for index_sql in indexes:
                cursor.execute(index_sql)
            
            conn.commit()
            logger.info(f"Database initialized at {self.db_path}")
    
    def add_tracks(self, tracks: List[Tuple[str, str, str, str, str]]) -> int:
        """
        Add tracks to database, avoiding duplicates
        
        Args:
            tracks: List of tuples (date_played, time_played, track_id, track_name, artist_name)
        
        Returns:
            Number of tracks actually inserted (excluding duplicates)
        """
        if not tracks:
            return 0
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Insert tracks, ignore duplicates
                cursor.executemany('''
                    INSERT OR IGNORE INTO tracks 
                    (date_played, time_played, track_id, track_name, artist_name)
                    VALUES (?, ?, ?, ?, ?)
                ''', tracks)
                
                inserted_count = cursor.rowcount
                
                # Update artist statistics
                if inserted_count > 0:
                    cursor.execute('''
                        INSERT OR REPLACE INTO artists (artist_name, total_plays)
                        SELECT artist_name, COUNT(*) as total_plays
                        FROM tracks
                        GROUP BY artist_name
                    ''')
                
                conn.commit()
                logger.info(f"Inserted {inserted_count} new tracks")
                return inserted_count
                
        except sqlite3.Error as e:
            logger.error(f"Database error adding tracks: {e}")
            return 0
        except Exception as e:
            logger.error(f"Unexpected error adding tracks: {e}")
            return 0
    
    def get_track_frequencies(self, limit: Optional[int] = None) -> List[Tuple]:
        """Get tracks ordered by play frequency"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                query = '''
                    SELECT track_id, track_name, artist_name, COUNT(*) as frequency
                    FROM tracks
                    GROUP BY track_id, track_name, artist_name
                    ORDER BY frequency DESC, track_name ASC
                '''
                
                if limit:
                    query += f' LIMIT {limit}'
                
                cursor.execute(query)
                return cursor.fetchall()
                
        except sqlite3.Error as e:
            logger.error(f"Database error getting track frequencies: {e}")
            return []
    
    def get_artist_frequencies(self) -> List[Tuple]:
        """Get artists ordered by total plays"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT artist_name, COUNT(*) as frequency
                    FROM tracks
                    GROUP BY artist_name
                    ORDER BY frequency DESC, artist_name ASC
                ''')
                
                return cursor.fetchall()
                
        except sqlite3.Error as e:
            logger.error(f"Database error getting artist frequencies: {e}")
            return []
    
    def get_playlist_tracks(self, num_songs: int) -> List[str]:
        """
        Get track IDs for playlist creation using your original logic
        Returns list of track_ids
        """
        try:
            track_frequencies = self.get_track_frequencies(num_songs * 2)  # Get extra for selection
            
            if not track_frequencies:
                return []
            
            if len(track_frequencies) <= num_songs:
                return [row[0] for row in track_frequencies]
            
            # Group tracks by frequency (your original logic)
            freq_groups = {}
            for track_id, track_name, artist_name, freq in track_frequencies:
                if freq not in freq_groups:
                    freq_groups[freq] = []
                freq_groups[freq].append((track_id, artist_name))
            
            track_ids = []
            frequencies = sorted(freq_groups.keys(), reverse=True)
            
            # Add all tracks except from the lowest frequency group
            for freq in frequencies[:-1]:
                for track_id, artist_name in freq_groups[freq]:
                    if len(track_ids) < num_songs:
                        track_ids.append(track_id)
            
            # Handle remaining slots with lowest frequency songs
            if len(track_ids) < num_songs and frequencies:
                remaining_slots = num_songs - len(track_ids)
                lowest_freq_songs = freq_groups[frequencies[-1]]
                
                # Sort by artist frequency for tie-breaking
                artist_freqs = dict(self.get_artist_frequencies())
                lowest_freq_songs.sort(key=lambda x: artist_freqs.get(x[1], 0))
                
                for track_id, _ in lowest_freq_songs[:remaining_slots]:
                    track_ids.append(track_id)
            
            return track_ids[:num_songs]
            
        except Exception as e:
            logger.error(f"Error generating playlist tracks: {e}")
            return []
    
    def get_statistics(self) -> Dict:
        """Get database statistics"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Basic counts
                cursor.execute("SELECT COUNT(*) FROM tracks")
                total_plays = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(DISTINCT track_id) FROM tracks")
                unique_tracks = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(DISTINCT artist_name) FROM tracks")
                unique_artists = cursor.fetchone()[0]
                
                # Date range
                cursor.execute("SELECT MIN(date_played), MAX(date_played) FROM tracks")
                date_range = cursor.fetchone()
                
                # Most played track
                cursor.execute('''
                    SELECT track_name, artist_name, COUNT(*) as plays
                    FROM tracks
                    GROUP BY track_id
                    ORDER BY plays DESC
                    LIMIT 1
                ''')
                most_played = cursor.fetchone()
                
                # Most played artist
                cursor.execute('''
                    SELECT artist_name, COUNT(*) as plays
                    FROM tracks
                    GROUP BY artist_name
                    ORDER BY plays DESC
                    LIMIT 1
                ''')
                most_played_artist = cursor.fetchone()
                
                return {
                    'total_plays': total_plays,
                    'unique_tracks': unique_tracks,
                    'unique_artists': unique_artists,
                    'date_range': date_range,
                    'most_played_track': most_played,
                    'most_played_artist': most_played_artist
                }
                
        except sqlite3.Error as e:
            logger.error(f"Error getting statistics: {e}")
            return {}
    
    def cleanup_old_data(self, days_to_keep: int = 90) -> int:
        """Remove data older than specified days"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).date()
                
                cursor.execute('''
                    DELETE FROM tracks 
                    WHERE date_played < ?
                ''', (cutoff_date,))
                
                deleted_count = cursor.rowcount
                
                # Update artist statistics
                if deleted_count > 0:
                    cursor.execute('''
                        UPDATE artists SET total_plays = (
                            SELECT COUNT(*) FROM tracks WHERE tracks.artist_name = artists.artist_name
                        )
                    ''')
                    
                    # Remove artists with no tracks
                    cursor.execute('DELETE FROM artists WHERE total_plays = 0')
                
                conn.commit()
                logger.info(f"Cleaned up {deleted_count} old records")
                return deleted_count
                
        except sqlite3.Error as e:
            logger.error(f"Error cleaning up old data: {e}")
            return 0
    
    def backup_database(self, backup_name: str = None) -> str:
        """Create a backup of the database"""
        try:
            if not backup_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"spotify_backup_{timestamp}.db"
            
            backup_path = Path(config.BACKUP_DIR) / backup_name
            shutil.copy2(self.db_path, backup_path)
            
            logger.info(f"Database backed up to {backup_path}")
            return str(backup_path)
            
        except Exception as e:
            logger.error(f"Error backing up database: {e}")
            return ""
    
    def import_from_csv(self, csv_file_path: str) -> int:
        """Import data from your existing CSV files"""
        import csv
        
        try:
            tracks_to_add = []
            
            with open(csv_file_path, 'r', newline='', encoding='utf-8') as file:
                reader = csv.reader(file)
                next(reader)  # Skip header
                
                for row in reader:
                    if len(row) >= 5:
                        # Assuming format: date, time, track_id, track_name, artist_name
                        tracks_to_add.append((row[0], row[1], row[2], row[3], row[4]))
            
            if tracks_to_add:
                return self.add_tracks(tracks_to_add)
            
            return 0
            
        except Exception as e:
            logger.error(f"Error importing from CSV: {e}")
            return 0