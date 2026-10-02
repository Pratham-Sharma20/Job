"""
PayPal Careers Scraper.
Scrapes PayPal Careers (https://paypal.eightfold.ai/careers)
Extracts software engineering, backend, frontend, and early-career opportunities in India via Eightfold PCSX API.
"""

import os
import sys
import requests
from typing import Optional

# Ensure backend root is on sys.path
backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from pipeline import process_jobs_batch, PipelineMetrics


def scrape_paypal(metrics: Optional[PipelineMetrics] = None) -> PipelineMetrics:
    """Scrapes PayPal for software and tech jobs in India via Eightfold PCSX API."""
    if metrics is None:
        metrics = PipelineMetrics("PayPal")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
    }

    queries = [
        "software",
        "intern",
        "engineer",
        "developer",
        "data",
        "ai",
        "backend",
        "frontend",
        ""
    ]

    seen_ids = set()

    for q in queries:
        start = 0
        while start < 100:  # Paginate up to 100 results per query
            url = f"https://paypal.eightfold.ai/api/pcsx/search?domain=paypal.com&query={q}&location=India&start={start}"
            try:
                res = requests.get(url, headers=headers, timeout=15)
                if res.status_code != 200:
                    break

                data = res.json()
                positions = data.get("data", {}).get("positions", [])
                if not positions:
                    break

                raw_jobs = []
                for pos in positions:
                    job_id = str(pos.get("id") or pos.get("atsJobId") or "")
                    if not job_id or job_id in seen_ids:
                        continue
                    seen_ids.add(job_id)

                    title = pos.get("name", "")
                    locations = pos.get("locations", [])
                    loc_str = ", ".join(locations) if locations else "India"

                    pos_url = pos.get("positionUrl", "")
                    if pos_url and not pos_url.startswith("http"):
                        apply_link = f"https://paypal.eightfold.ai{pos_url}"
                    else:
                        apply_link = pos_url or f"https://paypal.eightfold.ai/careers/job/{job_id}"

                    department = pos.get("department", "")

                    is_early_career = any(
                        kw in title.lower()
                        for kw in ["intern", "university", "graduate", "entry level", "fresher", "associate", "trainee"]
                    )

                    raw_jobs.append({
                        "job_id": f"paypal-{job_id}",
                        "company": "PayPal",
                        "title": title,
                        "location": loc_str,
                        "country": "India",
                        "experience_text": "0-1 years" if is_early_career else "",
                        "apply_link": apply_link,
                        "description": f"Department: {department}. Location: {loc_str}",
                        "source": "PayPal Eightfold",
                    })

                if raw_jobs:
                    process_jobs_batch(raw_jobs, metrics)

                start += 10
            except Exception as e:
                print(f"PayPal fetch query '{q}' at start {start} failed: {e}")
                break

    metrics.finish(status="SUCCESS")
    return metrics


if __name__ == "__main__":
    m = scrape_paypal()
    print(m.summary_line())
