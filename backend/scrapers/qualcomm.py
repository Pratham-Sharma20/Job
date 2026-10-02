"""
Qualcomm Careers Scraper.
Scrapes Qualcomm Careers (https://careers.qualcomm.com/careers) via official PCSX REST API.
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


def scrape_qualcomm(metrics: Optional[PipelineMetrics] = None) -> PipelineMetrics:
    """Scrapes Qualcomm Careers for software and tech jobs in India."""
    if metrics is None:
        metrics = PipelineMetrics("Qualcomm")

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
        "modem",
        "ai",
        "hardware",
        "systems"
    ]

    seen_ids = set()

    for q in queries:
        offset = 0
        limit = 20
        while offset < 100:  # Cap at top 100 results per query
            url = f"https://careers.qualcomm.com/api/pcsx/search?domain=qualcomm.com&query={q}&location=India&start={offset}&num={limit}"
            try:
                res = requests.get(url, headers=headers, timeout=15)
                if res.status_code != 200:
                    break

                data = res.json().get("data", {})
                positions = data.get("positions", [])
                if not positions:
                    break

                raw_jobs = []
                for p in positions:
                    pid = str(p.get("id") or p.get("atsJobId") or p.get("displayJobId") or "").strip()
                    if not pid or pid in seen_ids:
                        continue
                    seen_ids.add(pid)

                    title = p.get("name", "").strip()
                    locations = p.get("locations", [])
                    loc_str = ", ".join(locations) if locations else "India"
                    dept = p.get("department", "")

                    pos_url = p.get("positionUrl", "")
                    if pos_url.startswith("/"):
                        link = f"https://careers.qualcomm.com{pos_url}"
                    elif pos_url.startswith("http"):
                        link = pos_url
                    else:
                        link = f"https://careers.qualcomm.com/careers/job/{pid}"

                    is_early_career = any(
                        kw in title.lower()
                        for kw in ["intern", "graduate", "entry level", "fresher", "associate", "trainee"]
                    )

                    raw_jobs.append({
                        "job_id": f"qualcomm-{pid}",
                        "company": "Qualcomm",
                        "title": title,
                        "location": loc_str,
                        "country": "India",
                        "experience_text": "0-1 years" if is_early_career else "",
                        "apply_link": link,
                        "description": f"Department: {dept}" if dept else "",
                        "source": "Qualcomm Careers",
                    })

                if raw_jobs:
                    process_jobs_batch(raw_jobs, metrics)

                offset += limit
                count = data.get("count", 0)
                if offset >= count:
                    break

            except Exception as e:
                print(f"Error fetching Qualcomm jobs for query '{q}' offset {offset}: {e}")
                break

    metrics.finish(status="SUCCESS")
    return metrics


if __name__ == "__main__":
    m = scrape_qualcomm()
    print(m.summary_line())
