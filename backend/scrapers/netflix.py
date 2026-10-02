"""
Netflix Careers Scraper.
Scrapes Netflix Careers (https://explore.jobs.netflix.net/careers) via official Eightfold REST API.
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


def scrape_netflix(metrics: Optional[PipelineMetrics] = None) -> PipelineMetrics:
    """Scrapes Netflix Careers for software and tech jobs in India."""
    if metrics is None:
        metrics = PipelineMetrics("Netflix")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json",
    }

    queries = [
        "software",
        "engineer",
        "data",
        "intern",
        "developer",
        "platform",
        "infrastructure"
    ]

    seen_ids = set()

    # 1. Location-based search for India
    urls = [
        "https://explore.jobs.netflix.net/api/apply/v2/jobs?domain=netflix.com&location=India&num=50",
    ] + [
        f"https://explore.jobs.netflix.net/api/apply/v2/jobs?domain=netflix.com&query={q}&num=50"
        for q in queries
    ]

    for url in urls:
        try:
            res = requests.get(url, headers=headers, timeout=15)
            if res.status_code != 200:
                continue

            data = res.json()
            positions = data.get("positions", []) or data.get("jobs", [])
            if not positions:
                continue

            raw_jobs = []
            for p in positions:
                pid = str(p.get("id") or p.get("ats_job_id") or p.get("display_job_id") or "").strip()
                if not pid or pid in seen_ids:
                    continue
                seen_ids.add(pid)

                title = p.get("name") or p.get("posting_name") or ""
                locations = p.get("locations", []) or [p.get("location", "India")]
                loc_str = ", ".join(locations)
                dept = p.get("department", "")

                link = p.get("canonicalPositionUrl") or f"https://explore.jobs.netflix.net/careers/job/{pid}"

                is_early_career = any(
                    kw in title.lower()
                    for kw in ["intern", "graduate", "entry level", "fresher", "associate"]
                )

                raw_jobs.append({
                    "job_id": f"netflix-{pid}",
                    "company": "Netflix",
                    "title": title,
                    "location": loc_str,
                    "country": "India" if any("india" in loc.lower() for loc in locations) else "",
                    "experience_text": "0-1 years" if is_early_career else "",
                    "apply_link": link,
                    "description": f"Department: {dept}" if dept else "",
                    "source": "Netflix Careers",
                })

            if raw_jobs:
                process_jobs_batch(raw_jobs, metrics)

        except Exception as e:
            print(f"Error fetching Netflix jobs from {url}: {e}")

    metrics.finish(status="SUCCESS")
    return metrics


if __name__ == "__main__":
    m = scrape_netflix()
    print(m.summary_line())
