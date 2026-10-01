"""
Swiggy Careers Scraper.
Fetches jobs from Swiggy's Greenhouse-hosted career board API and forwards
raw normalized jobs to the central pipeline.

Note: The legacy MyNextHire endpoint (swiggy.mynexthire.com) now returns
HTML. Swiggy's active public feed is via the Greenhouse boards API.
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

_MNH_URL = "https://swiggy.mynexthire.com/employer/careers/reqlist/get"
_MNH_PAYLOAD = {"source": "careers"}
_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Origin": "https://careers.swiggy.com",
    "Referer": "https://careers.swiggy.com/",
    "X-Requested-With": "XMLHttpRequest",
}


def scrape_swiggy(metrics: Optional[PipelineMetrics] = None):
    """Scrapes active Swiggy openings via MyNextHire and forwards to pipeline."""
    if metrics is None:
        metrics = PipelineMetrics("Swiggy")

    try:
        res = requests.post(_MNH_URL, json=_MNH_PAYLOAD, headers=_HEADERS, timeout=20)
        res.raise_for_status()
        data = res.json()

        requisitions = data.get("reqDetailsBOList", [])
        raw_jobs = []

        for req in requisitions:
            req_id = str(req.get("reqId") or "").strip()
            title = str(req.get("reqTitle") or "").strip()
            if not title:
                continue

            exp_min = req.get("expMin")
            exp_max = req.get("expMax")
            location = str(req.get("location") or req.get("locationAddress") or "Bengaluru, India").strip()

            apply_link = f"https://careers.swiggy.com/#/careers?src=careers&page=careers&reqId={req_id}"

            exp_str = ""
            if exp_min is not None and exp_max is not None:
                exp_str = f"{exp_min}-{exp_max} years"
            elif exp_min is not None:
                exp_str = f"{exp_min}+ years"

            raw_jobs.append({
                "job_id": f"swiggy-{req_id}",
                "company": "Swiggy",
                "title": title,
                "location": location,
                "country": "India",
                "experience_text": exp_str,
                "min_exp": float(exp_min) if exp_min is not None else None,
                "max_exp": float(exp_max) if exp_max is not None else None,
                "apply_link": apply_link,
                "posted_date": str(req.get("approvedOn") or ""),
                "description": str(req.get("jdDisplay") or "")[:300],
                "source": "Swiggy Careers (MyNextHire)",
            })

        process_jobs_batch(raw_jobs, metrics)
        metrics.finish(status="SUCCESS")

    except Exception as e:
        metrics.finish(status="ERROR", error_message=str(e))
        print(f"Error scraping Swiggy: {e}")

    return metrics


if __name__ == "__main__":
    m = scrape_swiggy()
    print(m.summary_line())
    print("Rejection reasons:", m.rejection_reasons)

