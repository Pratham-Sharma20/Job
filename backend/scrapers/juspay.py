"""
Juspay Careers Scraper.
Extracts job listings from the SSR-rendered HTML at https://juspay.io/careers.
Job data is embedded as HTML-entity-encoded JSON blobs (React Fusion format)
directly in the page HTML - no Playwright needed.

Fields extracted: job_id, job_title, job_location, job_type, category,
                  experience_year, is_global, opening_status
"""

import os
import sys
import re
import json
import html as html_mod
import requests
from typing import Optional

backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from pipeline import process_jobs_batch, PipelineMetrics

_BASE_URL = "https://juspay.io"
_CAREERS_URL = f"{_BASE_URL}/careers"
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
}

# Regex to find individual job blobs in the encoded HTML
# Each job has: job_id, job_title, job_location, job_type, opening_status
_JOB_PATTERN = re.compile(
    r'&quot;job_id&quot;:\[0,&quot;([^&]+)&quot;\]'
    r'.*?&quot;job_location&quot;:\[0,&quot;([^&]*)&quot;\]'
    r'.*?&quot;job_title&quot;:\[0,&quot;([^&]+)&quot;\]'
    r'.*?&quot;job_type&quot;:\[0,&quot;([^&]*)&quot;\]'
    r'.*?&quot;opening_status&quot;:\[0,(true|false)\]',
    re.DOTALL
)

# Also grab category and is_global (appear before job_id in the blob)
_CAT_PATTERN = re.compile(
    r'&quot;category&quot;:\[0,&quot;([^&]*)&quot;\]'
    r'.*?&quot;experience_year&quot;:\[0,(\d+)\]'
    r'.*?&quot;is_global&quot;:\[0,(true|false)\]',
    re.DOTALL
)


def _extract_jobs(html_text: str) -> list:
    """Parse job listings from Juspay's HTML-entity-encoded SSR payload."""
    jobs = []

    # Split the page into per-job chunks by finding each category/job_id pair
    # Each job starts with &quot;category&quot; and ends with &quot;opening_status&quot;
    chunks = re.split(r'(?=&quot;category&quot;:\[0,&quot;)', html_text)

    for chunk in chunks:
        cat_m = _CAT_PATTERN.search(chunk)
        job_m = _JOB_PATTERN.search(chunk)
        if not job_m:
            continue

        job_id   = html_mod.unescape(job_m.group(1))
        location = html_mod.unescape(job_m.group(2)) or "Bangalore"
        title    = html_mod.unescape(job_m.group(3))
        job_type = html_mod.unescape(job_m.group(4))  # "Full-Time", "Intern", etc.
        is_open  = job_m.group(5) == "true"

        if not is_open or not title:
            continue

        category   = html_mod.unescape(cat_m.group(1)) if cat_m else ""
        exp_years  = int(cat_m.group(2)) if cat_m else 0
        is_global  = (cat_m.group(3) == "true") if cat_m else False

        # Skip global-only roles (India tab filter)
        if is_global and "bangalore" not in location.lower() and "india" not in location.lower():
            continue

        apply_link = f"{_BASE_URL}/careers/{job_id}"

        # Build experience_text from job_type and exp_years
        if "intern" in job_type.lower():
            exp_text = "intern"
        elif exp_years == 0:
            exp_text = "0-1 years"
        else:
            exp_text = f"{exp_years}+ years"

        jobs.append({
            "job_id": f"juspay-{job_id}",
            "company": "Juspay",
            "title": title,
            "location": f"{location}, India" if "india" not in location.lower() else location,
            "country": "India",
            "experience_text": exp_text,
            "min_exp": 0.0 if exp_years == 0 else float(exp_years),
            "max_exp": 1.0 if exp_years == 0 else None,
            "apply_link": apply_link,
            "description": f"Category: {category} | Type: {job_type}",
            "source": "Juspay Careers",
        })

    return jobs


def scrape_juspay(metrics: Optional[PipelineMetrics] = None):
    """Scrapes Juspay careers from SSR HTML and forwards raw jobs to pipeline."""
    if metrics is None:
        metrics = PipelineMetrics("Juspay")

    try:
        res = requests.get(_CAREERS_URL, headers=_HEADERS, timeout=20)
        res.raise_for_status()

        raw_jobs = _extract_jobs(res.text)

        if not raw_jobs:
            print("Juspay: no jobs found in SSR payload - page structure may have changed")

        process_jobs_batch(raw_jobs, metrics)
        metrics.finish(status="SUCCESS")

    except Exception as e:
        metrics.finish(status="ERROR", error_message=str(e))
        print(f"Error scraping Juspay: {e}")

    return metrics


if __name__ == "__main__":
    m = scrape_juspay()
    print(m.summary_line())
    print("Rejection reasons:", m.rejection_reasons)
