#!/usr/bin/env python3
"""
Cron Job Script for YouTube Agent.
Runs every 10 minutes and uploads videos about world locations.

Usage:
    python cron_job.py              # Run once
    python cron_job.py --daemon     # Run continuously every 10 minutes
    python cron_job.py --test       # Test mode (no upload)
"""

import sys
import time
import signal
import argparse
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from locations_data import get_random_topic
from main import YouTubeAgent
from utils.logger import get_logger
from config import settings

logger = get_logger("cron_job", settings.log_level, settings.log_file)

# Track used topics to avoid repetition
USED_TOPICS_FILE = Path(__file__).parent / "output" / "used_topics.txt"


def load_used_topics():
    """Load previously used topics."""
    if USED_TOPICS_FILE.exists():
        return set(USED_TOPICS_FILE.read_text().strip().split("\n"))
    return set()


def save_used_topic(topic):
    """Save a topic to the used list."""
    USED_TOPICS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(USED_TOPICS_FILE, "a") as f:
        f.write(f"{topic}\n")


def get_unique_topic(max_attempts=50):
    """Get a topic that hasn't been used recently."""
    used_topics = load_used_topics()
    
    for _ in range(max_attempts):
        topic = get_random_topic()
        if topic not in used_topics:
            return topic
    
    # If all topics used, clear history and start fresh
    logger.warning("All topics used, clearing history")
    USED_TOPICS_FILE.unlink(missing_ok=True)
    return get_random_topic()


def run_video_creation(upload=True):
    """Run the video creation pipeline with a random location topic."""
    topic = get_unique_topic()
    
    logger.info("=" * 60)
    logger.info(f"CRON JOB: Starting video creation")
    logger.info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Topic: {topic}")
    logger.info("=" * 60)
    
    try:
        agent = YouTubeAgent()
        result = agent.create_video_from_topic(topic, upload=upload)
        
        if result:
            save_used_topic(topic)
            logger.info(f"SUCCESS: Video created for '{topic}'")
            if result.get("video_id"):
                logger.info(f"YouTube URL: https://www.youtube.com/watch?v={result['video_id']}")
            return True
        else:
            logger.error(f"FAILED: Could not create video for '{topic}'")
            return False
            
    except Exception as e:
        logger.error(f"ERROR: {e}")
        return False


def run_daemon(interval_minutes=10):
    """Run continuously at specified interval."""
    logger.info(f"Starting daemon mode - running every {interval_minutes} minutes")
    logger.info("Press Ctrl+C to stop")
    
    # Handle graceful shutdown
    running = True
    
    def signal_handler(sig, frame):
        nonlocal running
        logger.info("Shutdown signal received, stopping...")
        running = False
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    while running:
        try:
            run_video_creation(upload=True)
        except Exception as e:
            logger.error(f"Error in daemon loop: {e}")
        
        if running:
            next_run = datetime.now().strftime('%H:%M:%S')
            logger.info(f"Next run in {interval_minutes} minutes (sleeping until then)...")
            
            # Sleep in small intervals to allow for graceful shutdown
            for _ in range(interval_minutes * 60):
                if not running:
                    break
                time.sleep(1)
    
    logger.info("Daemon stopped")


def main():
    parser = argparse.ArgumentParser(description="YouTube Agent Cron Job")
    parser.add_argument("--daemon", action="store_true", help="Run continuously every 10 minutes")
    parser.add_argument("--interval", type=int, default=10, help="Interval in minutes (default: 10)")
    parser.add_argument("--test", action="store_true", help="Test mode - don't upload to YouTube")
    
    args = parser.parse_args()
    
    if args.daemon:
        run_daemon(interval_minutes=args.interval)
    else:
        success = run_video_creation(upload=not args.test)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
