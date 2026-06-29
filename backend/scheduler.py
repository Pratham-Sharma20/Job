import schedule
import time
import subprocess
import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def run_scrapers():
    logging.info("Starting scheduled scrape job...")
    scraping_scripts = ["test.py", "ms.py", "google.py", "get_api.py"]
    
    for script in scraping_scripts:
        logging.info(f"Running {script}...")
        try:
            # Run the script using the same python interpreter
            result = subprocess.run([sys.executable, script], capture_output=True, text=True)
            logging.info(f"[{script}] finished with return code {result.returncode}")
            if result.stdout:
                logging.info(f"[{script}] Output:\n{result.stdout}")
            if result.stderr:
                logging.error(f"[{script}] Error:\n{result.stderr}")
        except Exception as e:
            logging.error(f"Failed to run {script}: {e}")

# Schedule the job to run every day at a specific time (e.g., midnight)
# You can change this time as needed
schedule.every().day.at("07:00").do(run_scrapers)

def run_scheduler():
    logging.info("Scheduler started in background thread. Waiting for scheduled jobs...")
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
