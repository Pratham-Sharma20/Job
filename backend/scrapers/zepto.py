"""
Zepto Careers Scraper.
Scrapes official openings from https://www.zepto.com/s/careers
Uses Playwright with fallback and isolates failures.
"""

import os
import sys
from typing import Optional

# Ensure backend root is on sys.path
backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from pipeline import process_jobs_batch, PipelineMetrics


def scrape_zepto(metrics: Optional[PipelineMetrics] = None):
    """Scrapes Zepto careers and forwards raw jobs to pipeline."""
    if metrics is None:
        metrics = PipelineMetrics("Zepto")

    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled"]
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
            page = context.new_page()

            captured_jobs = []

            def handle_response(response):
                if any(kw in response.url.lower() for kw in ["job", "career", "opening", "requisition", "talentrecruit"]):
                    try:
                        ct = response.headers.get("content-type", "")
                        if "json" in ct:
                            data = response.json()
                            if isinstance(data, list):
                                captured_jobs.extend(data)
                            elif isinstance(data, dict):
                                items = data.get("jobs") or data.get("data") or data.get("results") or []
                                if isinstance(items, list):
                                    captured_jobs.extend(items)
                    except Exception:
                        pass

            page.on("response", handle_response)

            try:
                page.goto("https://www.zepto.com/s/careers", timeout=20000, wait_until="load")
                page.wait_for_timeout(3000)
            except Exception as nav_e:
                print(f"Zepto navigation warning: {nav_e}")

            # Also check DOM for job cards if rendered
            dom_items = page.query_selector_all(".job-card, .career-item, [data-job-id]")
            raw_jobs = []

            for item in dom_items:
                title = item.inner_text().split("\n")[0].strip()
                link = item.get_attribute("href") or page.url
                raw_jobs.append({
                    "job_id": f"zepto-{title}".lower().replace(" ", "-"),
                    "company": "Zepto",
                    "title": title,
                    "location": "Bengaluru, India",
                    "country": "India",
                    "apply_link": link,
                    "source": "Zepto Careers",
                })

            for j in captured_jobs:
                if isinstance(j, dict):
                    t = str(j.get("title") or j.get("jobTitle") or "").strip()
                    l = str(j.get("applyUrl") or j.get("link") or page.url).strip()
                    if t:
                        raw_jobs.append({
                            "job_id": str(j.get("id") or l or f"zepto-{t}"),
                            "company": "Zepto",
                            "title": t,
                            "location": str(j.get("location") or "Bengaluru, India"),
                            "country": "India",
                            "apply_link": l,
                            "source": "Zepto Careers",
                        })

            browser.close()

        process_jobs_batch(raw_jobs, metrics)
        metrics.finish(status="SUCCESS")

    except Exception as e:
        metrics.finish(status="ERROR", error_message=str(e))
        print(f"Error in Zepto scraper: {e}")

    return metrics


if __name__ == "__main__":
    m = scrape_zepto()
    print(m.summary_line())
