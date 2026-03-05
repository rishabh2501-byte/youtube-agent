"""
AI YouTube Agent - Scheduler
Runs the video creation pipeline automatically on a daily schedule.
"""

import signal
import sys
from datetime import datetime
from typing import Optional

import schedule
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from config import settings
from utils.logger import get_logger
from main import YouTubeAgent

logger = get_logger(__name__, settings.log_level, settings.log_file)


class AgentScheduler:
    """
    Scheduler for running the YouTube Agent automatically.
    Supports both simple scheduling (schedule library) and cron-style (APScheduler).
    """
    
    def __init__(self):
        """Initialize the scheduler."""
        self.agent = None
        self.scheduler = None
        self.running = False
        
        logger.info("AgentScheduler initialized")
    
    def _create_agent(self) -> YouTubeAgent:
        """Create a new agent instance for each run."""
        return YouTubeAgent()
    
    def run_job(self) -> None:
        """Execute the video creation job."""
        logger.info("=" * 60)
        logger.info(f"Scheduled job started at {datetime.now().isoformat()}")
        logger.info("=" * 60)
        
        try:
            # Create fresh agent instance
            agent = self._create_agent()
            
            # Run the pipeline
            results = agent.run(upload=True, cleanup=True)
            
            if results:
                logger.info("Scheduled job completed successfully")
                logger.info(f"Video URL: {results.get('video_url', 'N/A')}")
            else:
                logger.error("Scheduled job failed")
                
        except Exception as e:
            logger.error(f"Scheduled job error: {e}")
    
    def start_simple_scheduler(self, time_str: Optional[str] = None) -> None:
        """
        Start a simple daily scheduler using the schedule library.
        
        Args:
            time_str: Time to run daily (HH:MM format), defaults to settings
        """
        time_str = time_str or settings.schedule_time
        
        logger.info(f"Starting simple scheduler - Daily at {time_str}")
        
        # Schedule the job
        schedule.every().day.at(time_str).do(self.run_job)
        
        # Also run immediately for testing
        logger.info("Running initial job...")
        self.run_job()
        
        self.running = True
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Run the scheduler loop
        logger.info("Scheduler running. Press Ctrl+C to stop.")
        while self.running:
            schedule.run_pending()
            import time
            time.sleep(60)  # Check every minute
    
    def start_cron_scheduler(
        self,
        hour: int = 9,
        minute: int = 0,
        timezone: Optional[str] = None
    ) -> None:
        """
        Start a cron-style scheduler using APScheduler.
        
        Args:
            hour: Hour to run (0-23)
            minute: Minute to run (0-59)
            timezone: Timezone for scheduling
        """
        timezone = timezone or settings.timezone
        
        logger.info(f"Starting cron scheduler - Daily at {hour:02d}:{minute:02d} ({timezone})")
        
        self.scheduler = BlockingScheduler(timezone=timezone)
        
        # Add the job with cron trigger
        self.scheduler.add_job(
            self.run_job,
            CronTrigger(hour=hour, minute=minute),
            id="daily_video_job",
            name="Daily Video Creation",
            replace_existing=True
        )
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("Scheduler running. Press Ctrl+C to stop.")
        
        try:
            self.scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            logger.info("Scheduler stopped")
    
    def _signal_handler(self, signum, frame) -> None:
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
        
        if self.scheduler:
            self.scheduler.shutdown(wait=False)
        
        sys.exit(0)
    
    def run_once(self) -> None:
        """Run the job once immediately (for testing)."""
        logger.info("Running single job execution...")
        self.run_job()


def parse_time(time_str: str) -> tuple[int, int]:
    """Parse time string (HH:MM) to hour and minute."""
    parts = time_str.split(":")
    return int(parts[0]), int(parts[1])


def main():
    """Main entry point for the scheduler."""
    import argparse
    
    parser = argparse.ArgumentParser(description="AI YouTube Agent Scheduler")
    parser.add_argument(
        "--time",
        type=str,
        default=settings.schedule_time,
        help="Time to run daily (HH:MM format)"
    )
    parser.add_argument(
        "--timezone",
        type=str,
        default=settings.timezone,
        help="Timezone for scheduling"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run once immediately and exit"
    )
    parser.add_argument(
        "--simple",
        action="store_true",
        help="Use simple scheduler instead of APScheduler"
    )
    
    args = parser.parse_args()
    
    scheduler = AgentScheduler()
    
    if args.once:
        scheduler.run_once()
    elif args.simple:
        scheduler.start_simple_scheduler(args.time)
    else:
        hour, minute = parse_time(args.time)
        scheduler.start_cron_scheduler(hour, minute, args.timezone)


if __name__ == "__main__":
    main()
