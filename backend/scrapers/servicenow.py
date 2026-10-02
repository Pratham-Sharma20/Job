"""
ServiceNow Careers Scraper.
Scrapes ServiceNow Careers (https://careers.servicenow.com) via official SmartRecruiters API.
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


def scrape_servicenow(metrics: Optional[PipelineMetrics] = None) -> PipelineMetrics:
    """Scrapes ServiceNow Careers for software and tech jobs in India."""
    if metrics is None:
        metrics = PipelineMetrics("ServiceNow")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json",
    }

    queries = [
        "software",
        "engineer",
        "intern",
        "developer",
        "cloud",
        "qa",
        "full stack"
    ]

    seen_ids = set()

    for q in queries:
        offset = 0
        limit = 50
        while offset < 200:
            url = f"https://api.smartrecruiters.com/v1/companies/servicenow/postings?q={q}&country=in&offset={offset}&limit={limit}"
            try:
                res = requests.get(url, headers=headers, timeout=15)
                if res.status_code != 200:
                    break

                data = res.json()
                postings = data.get("content", [])
                if not postings:
                    break

                raw_jobs = []
                for item in postings:
                    jid = str(item.get("id") or "").strip()
                    if not jid or jid in seen_ids:
                        continue
                    seen_ids.add(jid)

                    title = item.get("name", "").strip()
                    loc_obj = item.get("location", {})
                    city = loc_obj.get("city", "")
                    country = loc_obj.get("country", "") or "India"
                    location = f"{city}, {country}".strip(", ") if city else "India"

                    link = f"https://careers.servicenow.com/jobs/{jid}"
                    dept_obj = item.get("department", {})
                    dept_name = dept_obj.get("label", "") if isinstance(dept_obj, dict) else ""

                    is_early_career = any(
                        kw in title.lower()
                        for kw in ["intern", "graduate", "entry level", "fresher", "associate", "trainee"]
                    )

                    raw_jobs.append({
                        "job_id": f"servicenow-{jid}",
                        "company": "ServiceNow",
                        "title": title,
                        "location": location,
                        "country": "India",
                        "experience_text": "0-1 years" if is_early_career else "",
                        "apply_link": link,
                        "description": f"Department: {dept_name}" if dept_name else "",
                        "source": "ServiceNow Careers",
                    })

                if raw_jobs:
                    process_jobs_batch(raw_jobs, metrics)

                offset += limit
                total = data.get("totalFound", 0)
                if offset >= total:
                    break

            except Exception as e:
                print(f"Error fetching ServiceNow jobs for query '{q}': {e}")
                break

    metrics.finish(status="SUCCESS")
    return metrics


if __name__ == "__main__":
    m = scrape_servicenow()
    print(m.summary_line())
