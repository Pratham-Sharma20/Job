"""
Eternal (Zomato / Blinkit / District / Hyperpure) Careers Scraper.
Scrapes group careers from https://www.eternal.com/careers/ and maps positions
to explicit brand sub-entities.
"""

import os
import sys
import requests
from bs4 import BeautifulSoup
from typing import Optional

# Ensure backend root is on sys.path
backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from pipeline import process_jobs_batch, PipelineMetrics

BRANDS = ["Zomato", "Blinkit", "District", "Hyperpure"]


def scrape_eternal(metrics: Optional[PipelineMetrics] = None):
    """Scrapes Eternal group careers and forwards raw jobs to pipeline."""
    if metrics is None:
        metrics = PipelineMetrics("Eternal")

    url = "https://www.eternal.com/careers/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }

    raw_jobs = []

    try:
        res = requests.get(url, headers=headers, timeout=20)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            
            # Extract links or job cards
            job_elements = soup.find_all(["a", "div"], class_=lambda c: c and any(w in str(c).lower() for w in ["job", "role", "position", "career"]))
            
            for elem in job_elements:
                title = elem.get_text(strip=True)
                href = elem.get("href") or url
                link = href if href.startswith("http") else f"https://www.eternal.com{href}"

                # Infer brand if mentioned
                brand_matched = "Zomato"
                for b in BRANDS:
                    if b.lower() in title.lower() or b.lower() in link.lower():
                        brand_matched = b
                        break

                if title and len(title) < 100:
                    raw_jobs.append({
                        "job_id": f"eternal-{title}".lower().replace(" ", "-"),
                        "company": "Eternal",
                        "brand": brand_matched,
                        "title": title,
                        "location": "Gurugram / Bengaluru, India",
                        "country": "India",
                        "apply_link": link,
                        "source": f"Eternal ({brand_matched})",
                    })

        process_jobs_batch(raw_jobs, metrics)
        metrics.finish(status="SUCCESS")

    except Exception as e:
        metrics.finish(status="ERROR", error_message=str(e))
        print(f"Error scraping Eternal: {e}")

    return metrics


if __name__ == "__main__":
    m = scrape_eternal()
    print(m.summary_line())
