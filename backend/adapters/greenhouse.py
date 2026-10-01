"""
Greenhouse ATS Adapter.
Fetches jobs for Greenhouse-hosted career boards and forwards to the pipeline.
Supports optional India-location pre-filtering to avoid sending global roles
through the full pipeline when the board covers all regions.
"""

import requests
from typing import Optional
from pipeline import process_jobs_batch, PipelineMetrics

# Indian city/region tokens used to pre-filter Greenhouse job locations
_INDIA_OFFICE_TOKENS = [
    "india", "bengaluru", "bangalore", "hyderabad", "pune", "chennai",
    "mumbai", "delhi", "gurugram", "gurgaon", "noida", "kolkata",
    "karnataka", "telangana", "maharashtra", "remote, india",
]


def _is_india_office(location_name: str) -> bool:
    loc = location_name.lower()
    return any(token in loc for token in _INDIA_OFFICE_TOKENS)


def scrape_greenhouse_board(
    company: str,
    board: str,
    metrics: Optional[PipelineMetrics] = None,
    india_only: bool = False,
):
    """Scrapes a specific Greenhouse board and forwards raw jobs to pipeline.

    Args:
        india_only: When True, only jobs with an India office location are
                    forwarded to the pipeline. Useful for global boards like
                    Rubrik and Postman that list worldwide openings.
    """
    if metrics is None:
        metrics = PipelineMetrics(f"{company} (Greenhouse)")

    url = f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json"
    }

    try:
        res = requests.get(url, headers=headers, timeout=20)
        res.raise_for_status()
        data = res.json()

        raw_jobs = []
        skipped_non_india = 0
        for job in data.get("jobs", []):
            location_name = job.get("location", {}).get("name", "")

            if india_only and not _is_india_office(location_name):
                skipped_non_india += 1
                continue

            raw_jobs.append({
                "job_id": str(job.get("id") or job.get("absolute_url")),
                "company": company,
                "title": job.get("title", ""),
                "location": location_name,
                "country": "India" if india_only else "",
                "apply_link": job.get("absolute_url", ""),
                "posted_date": job.get("updated_at", ""),
                "source": "Greenhouse",
            })

        if india_only and skipped_non_india:
            print(f"  [{company}/Greenhouse] Pre-filtered {skipped_non_india} non-India offices")

        process_jobs_batch(raw_jobs, metrics)
        metrics.finish(status="SUCCESS")

    except Exception as e:
        metrics.finish(status="ERROR", error_message=str(e))
        print(f"Error scraping Greenhouse for {company} ({board}): {e}")

    return metrics
