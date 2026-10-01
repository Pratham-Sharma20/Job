"""
Myntra Careers Scraper.
Scrapes official openings from Myntra's careers portal (https://jobs.myntra.com/home)
and forwards raw normalized jobs to the central pipeline.
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


def scrape_myntra(metrics: Optional[PipelineMetrics] = None):
    """Scrapes Myntra careers and forwards raw jobs to pipeline."""
    if metrics is None:
        metrics = PipelineMetrics("Myntra")

    raw_jobs = []
    base_url = "https://jobs.myntra.com/home"

    try:
        # 1. Attempt API / structured retrieval
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }
        res = requests.get(base_url, headers=headers, timeout=20)
        res.raise_for_status()

        soup = BeautifulSoup(res.text, "html.parser")
        job_links = soup.find_all("a", href=True)

        for a in job_links:
            href = a["href"]
            text = a.get_text(strip=True)
            if any(k in href.lower() or k in text.lower() for k in ["job", "career", "engineer", "sde", "opening"]):
                raw_jobs.append({
                    "job_id": f"myntra-{text}".lower().replace(" ", "-"),
                    "company": "Myntra",
                    "title": text or "Software Engineer",
                    "location": "Bengaluru, India",
                    "country": "India",
                    "apply_link": href if href.startswith("http") else f"https://jobs.myntra.com/{href.lstrip('/')}",
                    "source": "Myntra Careers",
                })

        process_jobs_batch(raw_jobs, metrics)
        metrics.finish(status="SUCCESS")

    except Exception as e:
        metrics.finish(status="ERROR", error_message=str(e))
        print(f"Error scraping Myntra: {e}")

    return metrics


if __name__ == "__main__":
    m = scrape_myntra()
    print(m.summary_line())
