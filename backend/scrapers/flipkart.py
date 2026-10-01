"""
Flipkart Careers Scraper.
Scrapes https://www.flipkartcareers.com/jobslist and extracts technology / early career roles.
"""

import os
import sys
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from typing import Optional

# Ensure backend root is on sys.path
backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from pipeline import process_jobs_batch, PipelineMetrics

def scrape_flipkart(metrics: Optional[PipelineMetrics] = None):
    """Scrapes Flipkart careers jobslist and forwards to pipeline."""
    if metrics is None:
        metrics = PipelineMetrics("Flipkart")

    url = "https://www.flipkartcareers.com/jobslist"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }

    try:
        res = requests.get(url, headers=headers, timeout=20)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")

        raw_jobs = []
        job_items = soup.find_all(class_="job-item")

        for item in job_items:
            h6 = item.find("h6")
            title = h6.get_text(strip=True) if h6 else ""
            if not title:
                continue

            loc_div = item.find(class_="location")
            loc_text = loc_div.get_text(strip=True).replace("Location :", "").strip() if loc_div else "Bengaluru, India"

            # Check if there is an explicit link
            a_tag = item.find("a")
            if a_tag and a_tag.get("href"):
                href = a_tag.get("href")
                link = href if href.startswith("http") else f"https://www.flipkartcareers.com/{href.lstrip('/')}"
            else:
                # Direct canonical search URL for the position
                link = f"https://www.flipkartcareers.com/jobslist?search={quote_plus(title)}"

            # Flipkart jobs on this page are India tech/business roles
            raw_jobs.append({
                "job_id": f"flipkart-{title}-{loc_text}".lower().replace(" ", "-"),
                "company": "Flipkart",
                "title": title,
                "location": loc_text,
                "country": "India",
                "experience_text": "0-1 years" if any(w in title.lower() for w in ["intern", "graduate", "fresher", "entry", "sde 1", "sde i"]) else "",
                "apply_link": link,
                "source": "Flipkart Careers",
            })

        process_jobs_batch(raw_jobs, metrics)
        metrics.finish(status="SUCCESS")

    except Exception as e:
        metrics.finish(status="ERROR", error_message=str(e))
        print(f"Error scraping Flipkart: {e}")

    return metrics

if __name__ == "__main__":
    m = scrape_flipkart()
    print(m.summary_line())
