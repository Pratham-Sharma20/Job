"""
Cisco Careers Scraper.
Scrapes Cisco Career Portal (https://jobs.cisco.com / https://careers.cisco.com)
Extracts software engineering, infrastructure, AI/ML, and early-career roles using Playwright.
"""

import os
import sys
from typing import Optional, List, Dict, Any
from urllib.parse import quote_plus
from playwright.sync_api import sync_playwright

# Ensure backend root is on sys.path
backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from pipeline import process_jobs_batch, PipelineMetrics


def scrape_cisco(metrics: Optional[PipelineMetrics] = None) -> PipelineMetrics:
    """Scrapes Cisco Careers for software and tech jobs in India."""
    if metrics is None:
        metrics = PipelineMetrics("Cisco")

    queries = [
        "software",
        "intern",
        "engineer",
        "developer",
        "cloud",
        "security"
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

            for q in queries:
                url = f"https://careers.cisco.com/global/en/search-results?keywords={quote_plus(q)}"

                try:
                    page.goto(url, wait_until="networkidle", timeout=30000)
                except Exception:
                    try:
                        page.goto(url, wait_until="load", timeout=15000)
                    except Exception:
                        continue

                # Extract all job links
                job_links = page.query_selector_all("a[href*='/job/']")
                raw_jobs = []

                for link_el in job_links:
                    try:
                        href = link_el.get_attribute("href") or ""
                        title = link_el.inner_text().strip()
                        if not href or not title:
                            continue

                        # Extract Job ID from URL (e.g., https://careers.cisco.com/global/en/job/2022344/Software-Engineer)
                        parts = href.split("/job/")
                        if len(parts) > 1:
                            job_id_part = parts[1].split("/")[0]
                        else:
                            job_id_part = href

                        if not job_id_part or job_id_part in seen_ids:
                            continue
                        seen_ids.add(job_id_part)

                        # Check container text for location info
                        container_text = link_el.evaluate(
                            "el => el.closest('[data-ph-at-id=\"jobs-list-item\"], li, div.card') ? el.closest('[data-ph-at-id=\"jobs-list-item\"], li, div.card').innerText : ''"
                        )

                        is_early_career = any(
                            kw in title.lower()
                            for kw in ["intern", "university", "graduate", "entry level", "fresher", "co-op", "trainee"]
                        )

                        raw_jobs.append({
                            "job_id": f"cisco-{job_id_part}",
                            "company": "Cisco",
                            "title": title,
                            "location": "India",
                            "country": "India",
                            "experience_text": "0-1 years" if is_early_career else "",
                            "apply_link": href,
                            "description": container_text[:1000] if container_text else "",
                            "source": "Cisco Careers",
                        })
                    except Exception as parse_e:
                        print(f"Error parsing Cisco job link: {parse_e}")
                        continue

                if raw_jobs:
                    process_jobs_batch(raw_jobs, metrics)

            browser.close()

        metrics.finish(status="SUCCESS")

    except Exception as e:
        metrics.finish(status="ERROR", error_message=str(e))
        print(f"Error scraping Cisco Careers: {e}")

    return metrics


if __name__ == "__main__":
    m = scrape_cisco()
    print(m.summary_line())
