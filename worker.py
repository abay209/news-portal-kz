import os
import sys
from apscheduler.schedulers.blocking import BlockingScheduler
from rss_parser import fetch_rss_feeds

def run_worker():
    print("Starting background worker for RSS Parser...")
    
    # We use BlockingScheduler instead of BackgroundScheduler
    # because this script's sole purpose is to run the scheduler
    scheduler = BlockingScheduler()
    
    # Run immediately on start
    scheduler.add_job(func=fetch_rss_feeds, trigger="date")
    
    # Then every 5 minutes
    scheduler.add_job(func=fetch_rss_feeds, trigger="interval", minutes=5)
    
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("Worker stopped.")

if __name__ == '__main__':
    run_worker()
