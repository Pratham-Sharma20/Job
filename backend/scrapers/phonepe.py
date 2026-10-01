"""
PhonePe Careers Scraper.
Primary: PhonePe's SmartRecruiters ATS API (fast, robust, structured).
Fallback: Playwright DOM scraping if ATS API is unreachable.

Job cards contain: title, department/category, location, employment type, posted date.
"""

import os
import sys
import requests
from typing import Optional

backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from pipeline import process_jobs_batch, PipelineMetrics

_API_URL = "https://api.smartrecruiters.com/v1/companies/PHONEPELIMITED/postings?limit=100"
_CAREERS_URL = "https://www.phonepe.com/careers/job-openings/"
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json",
}

_TECH_DEPTS = {
    "engineering", "tech", "platform", "data", "ml", "ai",
    "machine learning", "backend", "frontend", "sde", "software",
    "infrastructure", "devops", "security", "mobile", "android", "ios",
    "tech infra & it",
}


def _is_tech_dept(dept: str) -> bool:
    d = dept.lower()
    return any(kw in d for kw in _TECH_DEPTS)


def scrape_phonepe_via_api() -> list:
    """Fetch jobs directly from PhonePe's SmartRecruiters API endpoint."""
    raw_jobs = []
    r = requests.get(_API_URL, headers=_HEADERS, timeout=15)
    if r.status_code != 200:
        return []

    data = r.json()
    postings = data.get("content", [])

    for item in postings:
        jid = str(item.get("id") or "").strip()
        title = str(item.get("name") or "").strip()
        if not title or not jid:
            continue

        # Extract Department Name from custom fields
        dept = ""
        for cf in item.get("customField", []):
            if cf.get("fieldLabel") == "Department Name":
                dept = cf.get("valueLabel", "")
                break

        # Location extraction
        loc_obj = item.get("location", {})
        loc = loc_obj.get("fullLocation") or loc_obj.get("city") or "Bengaluru, India"

        # Experience & Employment details
        exp_level = item.get("experienceLevel", {}).get("label", "")
        type_emp = item.get("typeOfEmployment", {}).get("label", "")
        exp_text = f"{title} {exp_level}".strip()

        apply_link = f"https://jobs.smartrecruiters.com/PHONEPELIMITED/{jid}"

        raw_jobs.append({
            "job_id": f"phonepe-{jid}",
            "company": "PhonePe",
            "title": title,
            "location": loc if "india" in loc.lower() or "bengaluru" in loc.lower() else f"{loc}, India",
            "country": "India",
            "experience_text": exp_text,
            "apply_link": apply_link,
            "description": f"Department: {dept} | Type: {type_emp} | Level: {exp_level}",
            "source": "PhonePe Careers",
        })

    return raw_jobs


def scrape_phonepe_via_playwright() -> list:
    """Fallback: scrape job cards using Playwright DOM."""
    raw_jobs = []
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 900},
            )
            page = context.new_page()

            try:
                page.goto(_CAREERS_URL, timeout=25000, wait_until="networkidle")
            except Exception:
                page.wait_for_timeout(4000)

            page.wait_for_timeout(2000)

            # PhonePe card selector: a.card inside .job-cards
            cards = page.query_selector_all("a.card, div.card, [class*='job-card']")

            for card in cards:
                try:
                    text_lines = [
                        ln.strip()
                        for ln in card.inner_text().split("\n")
                        if ln.strip()
                    ]
                    if len(text_lines) < 3:
                        continue

                    # In PhonePe cards:
                    # Line 0: Location (e.g. Bengaluru)
                    # Line 1: Dept (e.g. Engineering)
                    # Line 2: Title (e.g. Software Engineer - React Native)
                    # Line 3: Employment Type (Full-time)
                    loc = text_lines[0]
                    dept = text_lines[1]
                    title = text_lines[2]

                    # Extract link
                    href = card.get_attribute("href") or _CAREERS_URL
                    link = href if href.startswith("http") else f"https://www.phonepe.com{href}"

                    raw_jobs.append({
                        "job_id": f"phonepe-{title}-{loc}".lower().replace(" ", "-")[:80],
                        "company": "PhonePe",
                        "title": title,
                        "location": loc if "india" in loc.lower() else f"{loc}, India",
                        "country": "India",
                        "experience_text": title,
                        "apply_link": link,
                        "description": f"Department: {dept}",
                        "source": "PhonePe Careers",
                    })
                except Exception:
                    continue

            browser.close()
    except Exception as e:
        print(f"PhonePe Playwright fallback warning: {e}")

    return raw_jobs


def scrape_phonepe(metrics: Optional[PipelineMetrics] = None):
    """Scrapes PhonePe job openings and forwards to pipeline."""
    if metrics is None:
        metrics = PipelineMetrics("PhonePe")

    try:
        # Strategy 1: ATS API (fast and structured)
        raw_jobs = scrape_phonepe_via_api()

        # Strategy 2: Playwright DOM Fallback
        if not raw_jobs:
            raw_jobs = scrape_phonepe_via_playwright()

        process_jobs_batch(raw_jobs, metrics)
        metrics.finish(status="SUCCESS")

    except Exception as e:
        metrics.finish(status="ERROR", error_message=str(e))
        print(f"Error in PhonePe scraper: {e}")

    return metrics


if __name__ == "__main__":
    m = scrape_phonepe()
    print(m.summary_line())
    print("Rejection reasons:", m.rejection_reasons)
