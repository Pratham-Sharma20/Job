"""
Atlassian Careers Scraper.
Scrapes Atlassian Careers (https://www.atlassian.com/company/careers/all-jobs)
Extracts engineering, product, and early-career opportunities in India / Remote.
"""

import os
import sys
from typing import Optional
from playwright.sync_api import sync_playwright

# Ensure backend root is on sys.path
backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from pipeline import process_jobs_batch, PipelineMetrics


def scrape_atlassian(metrics: Optional[PipelineMetrics] = None) -> PipelineMetrics:
    """Scrapes Atlassian Careers for software and tech jobs in India."""
    if metrics is None:
        metrics = PipelineMetrics("Atlassian")

    url = "https://www.atlassian.com/company/careers/all-jobs"
    seen_ids = set()

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 800}
            )
            page = context.new_page()

            page.goto(url, wait_until="load", timeout=25000)
            page.wait_for_timeout(3000)

            rows = page.query_selector_all("tr[data-testid*='job-table-row'], tbody tr")
            raw_jobs = []

            for r in rows:
                try:
                    a = r.query_selector("a")
                    if not a:
                        continue
                    title = a.inner_text().strip()
                    href = a.get_attribute("href") or ""
                    if not title or not href:
                        continue

                    # Location column
                    loc_el = r.query_selector("td:nth-child(2)") or r.query_selector("[data-testid*='location']")
                    loc_text = loc_el.inner_text().strip() if loc_el else "India"

                    # Only filter for India / Remote jobs or all
                    is_india = any(
                        term in loc_text.lower()
                        for term in ["bengaluru", "bangalore", "india", "remote", "anywhere"]
                    )
                    if not is_india:
                        continue

                    job_id = href.rstrip("/").split("/")[-1]
                    if not job_id or job_id in seen_ids:
                        continue
                    seen_ids.add(job_id)

                    link = href if href.startswith("http") else f"https://www.atlassian.com{href}"

                    is_early_career = any(
                        kw in title.lower()
                        for kw in ["intern", "graduate", "entry level", "fresher", "associate"]
                    )

                    raw_jobs.append({
                        "job_id": f"atlassian-{job_id}",
                        "company": "Atlassian",
                        "title": title,
                        "location": loc_text,
                        "country": "India",
                        "experience_text": "0-1 years" if is_early_career else "",
                        "apply_link": link,
                        "description": f"Location: {loc_text}",
                        "source": "Atlassian Careers",
                    })
                except Exception as row_e:
                    print(f"Error parsing Atlassian job row: {row_e}")
                    continue

            if raw_jobs:
                process_jobs_batch(raw_jobs, metrics)

            browser.close()

        metrics.finish(status="SUCCESS")

    except Exception as e:
        metrics.finish(status="ERROR", error_message=str(e))
        print(f"Error scraping Atlassian: {e}")

    return metrics


if __name__ == "__main__":
    m = scrape_atlassian()
    print(m.summary_line())
