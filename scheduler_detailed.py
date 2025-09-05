# scheduler_detailed.py
import schedule
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
        """Check if the tracking run actually added new data"""
        try:
            if os.path.exists(TRACK_LOG_FILE):
                with open(TRACK_LOG_FILE, 'r') as f:
                    lines = len(f.readlines())
                self.logger.info(f"📊 Current track count: {lines-1}")  # -1 for header
        except Exception as e:
            self.logger.warning(f"Could not check data growth: {e}")
    
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
        print(f"   Next run: {schedule.next_run()}")
    
    def setup_schedules(self):
        """Configure different scheduling patterns"""
        
        # OPTION 1: Simple - Every 30 minutes
        schedule.every(30).minutes.do(self.run_tracker).tag('regular')
        
        # OPTION 2: Smart scheduling based on typical usage patterns
        
        # More frequent during typical listening hours
        schedule.every(15).minutes.do(self.run_tracker).tag('peak_hours')
        
        # Less frequent during sleep hours (12 AM - 7 AM)
        schedule.every().hour.do(self.run_tracker).tag('off_hours')
        
        # OPTION 3: Workday vs Weekend patterns
        # Weekdays: Every 20 minutes during work hours
        schedule.every(20).minutes.do(self.run_tracker).tag('workday')
        
        # Weekends: Every 30 minutes
        schedule.every(30).minutes.do(self.run_tracker).tag('weekend')
        
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
        try:
            if not os.path.exists(TRACK_LOG_FILE):
                return list(range(7, 24))  # Default: 7 AM to 11 PM
            
            import pandas as pd
            df = pd.read_csv(TRACK_LOG_FILE)
            
            if df.empty:
                return list(range(7, 24))
            
            # Convert time to hour
            df['hour'] = pd.to_datetime(df['Time'], format='%H:%M:%S').dt.hour
            
            # Find hours with listening activity
            active_hours = df['hour'].value_counts()
            
            # Hours with more than 5% of total listening
            threshold = len(df) * 0.05
            listening_hours = active_hours[active_hours > threshold].index.tolist()
            
            self.logger.info(f"🎯 Detected active listening hours: {listening_hours}")
            return listening_hours
            
        except Exception as e:
            self.logger.warning(f"Could not detect listening patterns: {e}")
            return list(range(7, 24))  # Fallback
    
    def setup_smart_schedules(self):
        """Set up schedules based on detected listening patterns"""
        current_hour = datetime.now().hour
        
        if current_hour in self.listening_hours:
            # Frequent checks during active hours
            schedule.every(15).minutes.do(self.run_tracker).tag('active')
            self.logger.info("📈 Using frequent schedule (active hours)")
        else:
            # Less frequent during inactive hours
            schedule.every(60).minutes.do(self.run_tracker).tag('inactive')
            self.logger.info("📉 Using reduced schedule (inactive hours)")

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
        schedule.clear()
        schedule.every(args.interval).minutes.do(scheduler.run_tracker)
    
    scheduler.start()

if __name__ == "__main__":
    main()

# =============================================================================
# WINDOWS SERVICE VERSION (Advanced)
# =============================================================================

# windows_service.py
import win32serviceutil
import win32service
import win32event
import servicemanager
import time
import sys
import os

class SpotifyTrackerService(win32serviceutil.ServiceFramework):
    """Windows service for Spotify tracking"""
    
    _svc_name_ = "SpotifyTracker"
    _svc_display_name_ = "Spotify Listening Tracker"
    _svc_description_ = "Automatically tracks Spotify listening history"
    
    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.is_running = True
        
    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        self.is_running = False
        
    def SvcDoRun(self):
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, '')
        )
        
        # Change to script directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(script_dir)
        
        # Start the scheduler
        scheduler = SpotifyScheduler()
        scheduler.setup_schedules()
        
        while self.is_running:
            schedule.run_pending()
            
            # Wait for stop signal or timeout
            rc = win32event.WaitForSingleObject(self.hWaitStop, 60000)  # 60 seconds
            if rc == win32event.WAIT_OBJECT_0:
                break

if __name__ == '__main__':
    if len(sys.argv) == 1:
        # Run as regular script
        main()
    else:
        # Handle service installation
        win32serviceutil.HandleCommandLine(SpotifyTrackerService)