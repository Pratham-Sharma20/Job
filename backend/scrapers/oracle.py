"""
Oracle Careers Scraper.
Scrapes Oracle Careers (https://careers.oracle.com/jobs) via official Oracle Cloud HCM REST API.
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


def scrape_oracle(metrics: Optional[PipelineMetrics] = None) -> PipelineMetrics:
    """Scrapes Oracle Careers for software and tech jobs in India."""
    if metrics is None:
        metrics = PipelineMetrics("Oracle")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json",
    }

    queries = [
        "software",
        "developer",
        "engineer",
        "intern",
        "cloud",
        "database",
        "infrastructure",
        "ai"
    ]

    seen_ids = set()

    for q in queries:
        url = (
            "https://eeho.fa.us2.oraclecloud.com/hcmRestApi/resources/latest/recruitingCEJobRequisitions"
            "?onlyData=true"
            "&expand=requisitionList.workLocation,requisitionList.otherWorkLocations,requisitionList.secondaryLocations,flexFieldsFacet.values,requisitionList.requisitionFlexFields"
            f'&finder=findReqs;siteNumber=CX_45001,facetsList=WORK_LOCATIONS%3BWORKPLACE_TYPES%3BTITLES%3BCATEGORIES%3BORGANIZATIONS%3BPOSTING_DATES%3BFLEX_FIELDS%3BLOCATIONS,limit=25,keyword="{q}",location=India,sortBy=RELEVANCY'
        )

        try:
            res = requests.get(url, headers=headers, timeout=15)
            if res.status_code != 200:
                continue

            data = res.json()
            items = data.get("items", [])
            if not items:
                continue

            reqs = items[0].get("requisitionList", [])
            raw_jobs = []

            for req in reqs:
                req_id = str(req.get("Id") or "").strip()
                if not req_id or req_id in seen_ids:
                    continue
                seen_ids.add(req_id)

                title = req.get("Title", "").strip()
                location = req.get("PrimaryLocation", "") or "India"
                posted_date = req.get("PostingDate", "")
                link = f"https://careers.oracle.com/en/sites/jobsearch/job/{req_id}"

                is_early_career = any(
                    kw in title.lower()
                    for kw in ["intern", "graduate", "entry level", "fresher", "associate", "trainee"]
                )

                raw_jobs.append({
                    "job_id": f"oracle-{req_id}",
                    "company": "Oracle",
                    "title": title,
                    "location": location,
                    "country": "India",
                    "experience_text": "0-1 years" if is_early_career else "",
                    "apply_link": link,
                    "posted_date": posted_date,
                    "source": "Oracle Careers",
                })

            if raw_jobs:
                process_jobs_batch(raw_jobs, metrics)

        except Exception as e:
            print(f"Error fetching Oracle jobs for query '{q}': {e}")

    metrics.finish(status="SUCCESS")
    return metrics


if __name__ == "__main__":
    m = scrape_oracle()
    print(m.summary_line())
