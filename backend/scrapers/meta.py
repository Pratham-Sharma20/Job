"""
Meta Careers Scraper.
Scrapes Meta Career Portal (https://www.metacareers.com/jobs)
Extracts software engineering, infrastructure, AI/ML, and early-career roles using Playwright GraphQL interception.
"""

import os
import sys
from urllib.parse import quote_plus
from typing import Optional, List, Dict, Any
from playwright.sync_api import sync_playwright

# Ensure backend root is on sys.path
backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from pipeline import process_jobs_batch, PipelineMetrics


def scrape_meta(metrics: Optional[PipelineMetrics] = None) -> PipelineMetrics:
    """Scrapes Meta Careers for tech and early-career opportunities in India."""
    if metrics is None:
        metrics = PipelineMetrics("Meta")

    # India offices and search targets on Meta Careers
    india_offices = [
        "Bangalore, India",
        "Gurgaon, India",
        "Hyderabad, India",
        "Mumbai, India",
        "New Delhi, India"
    ]

    target_urls = [
        # 1. Direct India offices query
        "https://www.metacareers.com/jobs?" + "&".join(
            [f"offices[{i}]={quote_plus(loc)}" for i, loc in enumerate(india_offices)]
        ),
        # 2. Targeted early-career & SWE searches
        "https://www.metacareers.com/jobs?q=intern",
        "https://www.metacareers.com/jobs?q=university",
        "https://www.metacareers.com/jobs?q=software%20engineer",
        "https://www.metacareers.com/jobs?q=production%20engineer",
    ]

    seen_ids = set()

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 800}
            )
            page = context.new_page()

            for url in target_urls:
                captured_jobs: List[Dict[str, Any]] = []

                def handle_response(response):
                    if "graphql" in response.url:
                        try:
                            data = response.json()
                            search_res = data.get("data", {}).get("job_search_with_featured_jobs_v2", {})
                            all_jobs = search_res.get("all_jobs", [])
                            if all_jobs:
                                captured_jobs.extend(all_jobs)
                        except Exception:
                            pass

                # Temporarily attach listener for this navigation
                page.on("response", handle_response)

                try:
                    page.goto(url, wait_until="networkidle", timeout=30000)
                except Exception as nav_e:
                    # Retry with load state if networkidle times out
                    try:
                        page.goto(url, wait_until="load", timeout=15000)
                    except Exception:
                        pass

                page.remove_listener("response", handle_response)

                raw_jobs = []
                for job in captured_jobs:
                    job_id = str(job.get("id", "")).strip()
                    if not job_id or job_id in seen_ids:
                        continue
                    seen_ids.add(job_id)

                    title = job.get("title", "").strip()
                    locations = job.get("locations", [])
                    loc_str = ", ".join(locations) if locations else "India"

                    teams = job.get("teams", [])
                    sub_teams = job.get("sub_teams", [])
                    desc_parts = []
                    if teams:
                        desc_parts.append(f"Teams: {', '.join(teams)}")
                    if sub_teams:
                        desc_parts.append(f"Subteams: {', '.join(sub_teams)}")
                    description = " | ".join(desc_parts)

                    is_early_career = any(
                        kw in title.lower()
                        for kw in ["intern", "university", "new grad", "early career", "entry level", "graduate"]
                    )

                    link = f"https://www.metacareers.com/jobs/{job_id}/"

                    raw_jobs.append({
                        "job_id": f"meta-{job_id}",
                        "company": "Meta",
                        "title": title,
                        "location": loc_str,
                        "country": "India" if any("india" in loc.lower() for loc in locations) else "",
                        "experience_text": "0-1 years" if is_early_career else "",
                        "apply_link": link,
                        "description": description,
                        "source": "Meta Careers",
                    })

                if raw_jobs:
                    process_jobs_batch(raw_jobs, metrics)

            browser.close()

        metrics.finish(status="SUCCESS")

    except Exception as e:
        metrics.finish(status="ERROR", error_message=str(e))
        print(f"Error scraping Meta Careers: {e}")

    return metrics


if __name__ == "__main__":
    m = scrape_meta()
    print(m.summary_line())
