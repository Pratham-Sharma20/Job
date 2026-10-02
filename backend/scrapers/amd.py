"""
AMD Careers Scraper.
Scrapes AMD Careers Portal (https://careers.amd.com) via official REST API.
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


def scrape_amd(metrics: Optional[PipelineMetrics] = None) -> PipelineMetrics:
    """Scrapes AMD Careers for software and tech jobs in India."""
    if metrics is None:
        metrics = PipelineMetrics("AMD")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json",
    }

    queries = [
        "software",
        "engineer",
        "intern",
        "developer",
        "firmware",
        "silicon",
        "gpu",
        "ai"
    ]

    seen_ids = set()

    for q in queries:
        page = 1
        while page <= 5:  # Cap at top 5 pages per query
            url = f"https://careers.amd.com/api/jobs?keywords={q}&location=India&page={page}&sortBy=relevance"
            try:
                res = requests.get(url, headers=headers, timeout=15)
                if res.status_code != 200:
                    break

                data = res.json()
                jobs = data.get("jobs", [])
                if not jobs:
                    break

                raw_jobs = []
                for job_obj in jobs:
                    j = job_obj.get("data", {})
                    req_id = str(j.get("req_id") or j.get("slug") or "").strip()
                    if not req_id or req_id in seen_ids:
                        continue
                    seen_ids.add(req_id)

                    title = j.get("title", "").strip()
                    city = j.get("city", "")
                    country = j.get("country", "") or "India"
                    location = j.get("full_location") or f"{city}, {country}".strip(", ")
                    link = j.get("meta_data", {}).get("canonical_url") or f"https://careers.amd.com/jobs/{req_id}"

                    is_early_career = any(
                        kw in title.lower()
                        for kw in ["intern", "graduate", "entry level", "fresher", "co-op", "trainee"]
                    )

                    raw_jobs.append({
                        "job_id": f"amd-{req_id}",
                        "company": "AMD",
                        "title": title,
                        "location": location,
                        "country": "India" if "india" in location.lower() else country,
                        "experience_text": "0-1 years" if is_early_career else "",
                        "apply_link": link,
                        "description": j.get("description", "")[:1000],
                        "source": "AMD Careers",
                    })

                if raw_jobs:
                    process_jobs_batch(raw_jobs, metrics)

                page += 1

            except Exception as e:
                print(f"Error fetching AMD jobs for query '{q}' page {page}: {e}")
                break

    metrics.finish(status="SUCCESS")
    return metrics


if __name__ == "__main__":
    m = scrape_amd()
    print(m.summary_line())
