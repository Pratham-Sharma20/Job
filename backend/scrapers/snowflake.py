"""
Snowflake Careers Scraper.
Scrapes Snowflake Careers (https://careers.snowflake.com)
Extracts software engineering, infrastructure, AI/ML, and early-career opportunities in India.
"""

import os
import sys
from typing import Optional
from urllib.parse import quote_plus
from playwright.sync_api import sync_playwright

# Ensure backend root is on sys.path
backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from pipeline import process_jobs_batch, PipelineMetrics


def scrape_snowflake(metrics: Optional[PipelineMetrics] = None) -> PipelineMetrics:
    """Scrapes Snowflake Careers for software and tech jobs in India."""
    if metrics is None:
        metrics = PipelineMetrics("Snowflake")

    queries = [
        "software",
        "intern",
        "engineer",
        "developer",
        "data",
        "cloud"
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
                url = f"https://careers.snowflake.com/us/en/search-results?keywords={quote_plus(q)}&location=India"
                try:
                    page.goto(url, wait_until="load", timeout=20000)
                    page.wait_for_timeout(3000)
                except Exception:
                    continue

                links = page.query_selector_all("a[href*='/job/'], [data-ph-at-id='job-link']")
                raw_jobs = []

                for link_el in links:
                    try:
                        href = link_el.get_attribute("href") or ""
                        title = link_el.inner_text().strip()
                        if not href or not title:
                            continue

                        # Extract Job ID
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

                        # Extract location text if available
                        loc_text = "India"
                        if container_text:
                            lines = [l.strip() for l in container_text.split("\n") if l.strip()]
                            for l in lines:
                                if any(t in l.lower() for t in ["india", "pune", "bangalore", "bengaluru", "hyderabad", "delhi", "mumbai"]):
                                    loc_text = l
                                    break
                                elif any(t in l.lower() for t in ["germany", "poland", "united states", "berlin", "warsaw", "amsterdam"]):
                                    loc_text = l
                                    break

                        is_early_career = any(
                            kw in title.lower()
                            for kw in ["intern", "university", "graduate", "entry level", "fresher", "associate"]
                        )

                        raw_jobs.append({
                            "job_id": f"snowflake-{job_id_part[:40]}",
                            "company": "Snowflake",
                            "title": title,
                            "location": loc_text,
                            "country": "India" if any(t in loc_text.lower() for t in ["india", "pune", "bangalore", "bengaluru", "hyderabad"]) else loc_text,
                            "experience_text": "0-1 years" if is_early_career else "",
                            "apply_link": href,
                            "description": container_text[:1000] if container_text else "",
                            "source": "Snowflake Careers",
                        })
                    except Exception as parse_e:
                        print(f"Error parsing Snowflake job link: {parse_e}")
                        continue

                if raw_jobs:
                    process_jobs_batch(raw_jobs, metrics)

            browser.close()

        metrics.finish(status="SUCCESS")

    except Exception as e:
        metrics.finish(status="ERROR", error_message=str(e))
        print(f"Error scraping Snowflake: {e}")

    return metrics


if __name__ == "__main__":
    m = scrape_snowflake()
    print(m.summary_line())
