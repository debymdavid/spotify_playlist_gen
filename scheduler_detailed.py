# scheduler_detailed.py
import schedule
import time  
import logging
import sys
import os
from datetime import datetime
from pathlib import Path

# Import your existing modules
try:
    from main import main as run_spotify_tracker
    from config import TRACK_LOG_FILE
except ImportError:
    print("❌ Error: Cannot import main modules. Make sure main.py and config.py exist.")
    sys.exit(1)

class SpotifyScheduler:
    """Advanced scheduler for automatic Spotify tracking"""
    
    def __init__(self):
        self.setup_logging()
        self.runs_today = 0
        self.successful_runs = 0
        self.failed_runs = 0
        self.start_time = datetime.now()
        
    def setup_logging(self):
        """Configure logging for scheduler"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / "scheduler.log"),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger("SpotifyScheduler")
        
    def run_tracker(self):
        """Execute the main tracking function with error handling"""
        run_start = datetime.now()
        self.runs_today += 1
        
        self.logger.info(f"🚀 Starting tracker run #{self.runs_today}")
        
        try:
            # Run your existing main function
            run_spotify_tracker()
            
            self.successful_runs += 1
            run_duration = (datetime.now() - run_start).total_seconds()
            
            self.logger.info(f"✅ Run #{self.runs_today} completed successfully in {run_duration:.1f}s")
            
            # Optional: Check if we got new data
            self.check_data_growth()
            
        except Exception as e:
            self.failed_runs += 1
            self.logger.error(f"❌ Run #{self.runs_today} failed: {str(e)}")
            
            # Optional: Send notification about failure
            self.handle_failure(e)
    
    def check_data_growth(self):
        from database import SpotifyDatabase
        db = SpotifyDatabase()
        conn = db.conn
        count = conn.execute("SELECT COUNT(*) FROM tracks").fetchone()[0]
        self.logger.info(f"📊 Current track count: {count}")
    
    def handle_failure(self, error):
        """Handle failed runs - could send notifications, etc."""
        self.logger.error(f"Failure details: {error}")
        
        # You could add email notifications, Discord webhooks, etc. here
        # Example:
        # send_discord_notification(f"Spotify tracker failed: {error}")
    
    def print_status(self):
        """Print current scheduler status"""
        uptime = datetime.now() - self.start_time
        success_rate = (self.successful_runs / max(self.runs_today, 1)) * 100
        
        print(f"\n📈 Scheduler Status:")
        print(f"   Uptime: {uptime}")
        print(f"   Total runs today: {self.runs_today}")
        print(f"   Successful: {self.successful_runs}")
        print(f"   Failed: {self.failed_runs}")
        print(f"   Success rate: {success_rate:.1f}%")
        
        try:
            next_run = schedule.next_run()
            if next_run:
                print(f"   Next run: {next_run}")
            else:
                print("   Next run: No jobs scheduled")
        except Exception:
            print("   Next run: Unable to determine")
    
    def setup_schedules(self):
        """Configure simple scheduling pattern"""
        # Clear any existing schedules
        schedule.clear()
        
        # Simple: Every 30 minutes
        schedule.every(30).minutes.do(self.run_tracker).tag('regular')
        
        self.logger.info("📅 Scheduling configured:")
        for job in schedule.get_jobs():
            self.logger.info(f"   {job}")
    
    def start(self):
        """Start the scheduler loop"""
        self.logger.info("🎵 Starting Spotify Tracker Scheduler...")
        self.logger.info(f"💾 Data will be saved to: {TRACK_LOG_FILE}")
        
        self.setup_schedules()
        
        # Run once immediately to test
        self.logger.info("🔄 Running initial test...")
        self.run_tracker()
        
        self.logger.info("⏰ Scheduler is now running. Press Ctrl+C to stop.")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
                # Print status every hour
                if datetime.now().minute == 0:
                    self.print_status()
                    
        except KeyboardInterrupt:
            self.logger.info("\n🛑 Scheduler stopped by user")
            self.print_status()
        except Exception as e:
            self.logger.error(f"💥 Scheduler crashed: {e}")
            raise

# Enhanced version with smart scheduling
class SmartSpotifyScheduler(SpotifyScheduler):
    """Intelligent scheduler that adapts based on listening patterns"""
    
    def __init__(self):
        super().__init__()
        self.listening_hours = self.detect_listening_patterns()
    
    def detect_listening_patterns(self):
        """Analyze existing data to determine when user typically listens"""
        from database import SpotifyDatabase
        import sqlite3
        db = SpotifyDatabase()
        rows = db.conn.execute("SELECT time_played FROM tracks").fetchall()
        if len(rows) < 10:
            return list(range(7, 24))
        hours = [int(r[0].split(":")[0]) for r in rows if r[0]]
        from collections import Counter
        counts = Counter(hours)
        threshold = len(rows) * 0.05
        active = sorted([h for h, c in counts.items() if c > threshold])
        return active or list(range(7, 24))
        
    
    def setup_schedules(self):
        """Set up schedules based on detected listening patterns"""
        schedule.clear()
        
        current_hour = datetime.now().hour
        
        if current_hour in self.listening_hours:
            # Frequent checks during active hours
            schedule.every(15).minutes.do(self.run_tracker).tag('active')
            self.logger.info("📈 Using frequent schedule (active hours) - every 15 minutes")
        else:
            # Less frequent during inactive hours
            schedule.every(60).minutes.do(self.run_tracker).tag('inactive')
            self.logger.info("📉 Using reduced schedule (inactive hours) - every 60 minutes")

# Command-line interface
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Spotify Tracker Scheduler')
    parser.add_argument('--mode', choices=['simple', 'smart'], default='simple',
                       help='Scheduling mode: simple (every 30min) or smart (adaptive)')
    parser.add_argument('--interval', type=int, default=30,
                       help='Minutes between runs (for simple mode)')
    parser.add_argument('--test', action='store_true',
                       help='Run once and exit (test mode)')
    
    args = parser.parse_args()
    
    if args.test:
        print("🧪 Test mode: Running tracker once...")
        scheduler = SpotifyScheduler()
        scheduler.run_tracker()
        print("✅ Test completed")
        return
    
    if args.mode == 'smart':
        print("🧠 Starting smart scheduler...")
        scheduler = SmartSpotifyScheduler()
    else:
        print(f"⏰ Starting simple scheduler (every {args.interval} minutes)...")
        scheduler = SpotifyScheduler()
        # Override the default setup_schedules for custom interval
        def custom_setup():
            schedule.clear()
            schedule.every(args.interval).minutes.do(scheduler.run_tracker).tag('custom')
            scheduler.logger.info(f"📅 Custom schedule: every {args.interval} minutes")
        
        scheduler.setup_schedules = custom_setup
    
    scheduler.start()

if __name__ == "__main__":
    main()