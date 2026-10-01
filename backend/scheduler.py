"""
Scheduler for automated periodic job scraping.
Executes master scraping runner with per-scraper failure isolation and health metric logging.
"""

import schedule
import time
import logging
from test import run_all_scrapers

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def run_scrapers():
    """Runs all scrapers with error isolation."""
    logging.info("Starting scheduled scrape run...")
    try:
        metrics = run_all_scrapers()
        successful = sum(1 for m in metrics if m.status == "SUCCESS")
        total = len(metrics)
        new_jobs = sum(m.new_jobs for m in metrics)
        logging.info(f"Scheduled run completed: {successful}/{total} scrapers successful, {new_jobs} new jobs discovered.")
    except Exception as e:
        logging.error(f"Fatal error during scheduled run: {e}", exc_info=True)


# Schedule daily scrape at 07:00 AM (customizable)
schedule.every().day.at("07:00").do(run_scrapers)


def run_scheduler():
    logging.info("Scheduler started. Waiting for scheduled jobs...")
    while True:
        schedule.run_pending()
        time.sleep(60)


def start_scheduler_thread():
    import threading
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()


if __name__ == "__main__":
    # If run directly as a script
    run_scheduler()
