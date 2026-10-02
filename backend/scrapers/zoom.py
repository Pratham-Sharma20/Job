"""
Zoom Careers Scraper.
Scrapes Zoom Careers (https://careers.zoom.us)
Extracts software engineering, infrastructure, AI/ML, and early-career opportunities via Playwright.
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


def scrape_zoom(metrics: Optional[PipelineMetrics] = None) -> PipelineMetrics:
    """Scrapes Zoom Careers for software and tech jobs in India."""
    if metrics is None:
        metrics = PipelineMetrics("Zoom")

    seen_ids = set()

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 800}
            )
            page = context.new_page()

            urls = [
                "https://www.careers.zoom.us/job-results#/",
                "https://www.careers.zoom.us/job-results#/?keyword=India",
                "https://www.careers.zoom.us/job-results#/?keyword=engineer",
                "https://www.careers.zoom.us/job-results#/?keyword=intern",
            ]

            for url in urls:
                try:
                    page.goto(url, wait_until="networkidle", timeout=25000)
                    page.wait_for_timeout(3000)
                except Exception:
                    try:
                        page.wait_for_timeout(2000)
                    except Exception:
                        continue

                links = page.query_selector_all("a[href*='/job-details/']")
                raw_jobs = []

                for link_el in links:
                    try:
                        href = link_el.get_attribute("href") or ""
                        title = link_el.inner_text().strip()
                        if not href or not title or title.lower() in ["read more", "apply", "share"]:
                            continue

                        # Canonical URL
                        if not href.startswith("http"):
                            href = f"https://www.careers.zoom.us{href}"

                        # Extract ID from slug
                        parts = href.split("-")
                        job_id_part = parts[-1].split("?")[0] if parts else href

                        if not job_id_part or job_id_part in seen_ids:
                            continue
                        seen_ids.add(job_id_part)

                        container_text = link_el.evaluate(
                            "el => el.closest('div, li, section') ? el.closest('div, li, section').innerText : ''"
                        )

                        loc_text = "India"
                        if container_text:
                            lines = [l.strip() for l in container_text.split("\n") if l.strip()]
                            for l in lines:
                                if any(t in l.lower() for t in ["india", "bangalore", "bengaluru", "mumbai", "delhi", "hyderabad", "pune", "chennai"]):
                                    loc_text = l
                                    break
                                elif any(t in l.lower() for t in ["united states", "remote", "singapore", "australia", "united kingdom", "ireland"]):
                                    loc_text = l
                                    break

                        is_early_career = any(
                            kw in title.lower()
                            for kw in ["intern", "university", "graduate", "entry level", "fresher", "associate"]
                        )

                        raw_jobs.append({
                            "job_id": f"zoom-{job_id_part}",
                            "company": "Zoom",
                            "title": title,
                            "location": loc_text,
                            "country": "India" if any(t in loc_text.lower() for t in ["india", "bangalore", "bengaluru", "hyderabad", "pune", "mumbai", "chennai"]) else loc_text,
                            "experience_text": "0-1 years" if is_early_career else "",
                            "apply_link": href,
                            "description": container_text[:1000] if container_text else "",
                            "source": "Zoom Careers",
                        })
                    except Exception as parse_e:
                        print(f"Error parsing Zoom job link: {parse_e}")
                        continue

                if raw_jobs:
                    process_jobs_batch(raw_jobs, metrics)

            browser.close()
    except Exception as e:
        print(f"Zoom Playwright browser scraping failed: {e}")
        metrics.finish(status="ERROR", error_message=str(e))
        return metrics

    metrics.finish(status="SUCCESS")
    return metrics


if __name__ == "__main__":
    m = scrape_zoom()
    print(m.summary_line())
