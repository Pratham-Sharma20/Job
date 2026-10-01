"""
Lever ATS Adapter.
Fetches jobs for Lever-hosted career boards and forwards to the pipeline.
"""

import requests
from typing import Optional
from pipeline import process_jobs_batch, PipelineMetrics

def scrape_lever_board(company: str, board: str, metrics: Optional[PipelineMetrics] = None):
    """Scrapes a specific Lever board and forwards raw jobs to pipeline."""
    if metrics is None:
        metrics = PipelineMetrics(f"{company} (Lever)")

    url = f"https://api.lever.co/v0/postings/{board}?mode=json"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json"
    }

    try:
        res = requests.get(url, headers=headers, timeout=20)
        res.raise_for_status()
        data = res.json()

        if not isinstance(data, list):
            metrics.finish(status="ERROR", error_message="Unexpected response format")
            return metrics

        raw_jobs = []
        for job in data:
            categories = job.get("categories", {})
            if not isinstance(categories, dict):
                categories = {}

            location = categories.get("location", "")
            raw_jobs.append({
                "job_id": str(job.get("id") or job.get("hostedUrl")),
                "company": company,
                "title": job.get("text", ""),
                "location": location,
                "country": "",
                "apply_link": job.get("hostedUrl", ""),
                "posted_date": str(job.get("createdAt", "")),
                "description": job.get("descriptionPlain", "")[:300],
                "source": "Lever",
            })

        process_jobs_batch(raw_jobs, metrics)
        metrics.finish(status="SUCCESS")

    except Exception as e:
        metrics.finish(status="ERROR", error_message=str(e))
        print(f"Error scraping Lever for {company} ({board}): {e}")

    return metrics
