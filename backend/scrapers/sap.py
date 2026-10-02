"""
SAP Careers Scraper.
Scrapes SAP Careers (https://jobs.sap.com)
Extracts software engineering, Cloud ERP, ABAP/HANA, AI, and early-career opportunities in India.
"""

import os
import sys
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from typing import Optional

# Ensure backend root is on sys.path
backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from pipeline import process_jobs_batch, PipelineMetrics


def scrape_sap(metrics: Optional[PipelineMetrics] = None) -> PipelineMetrics:
    """Scrapes SAP Careers for software and tech jobs in India."""
    if metrics is None:
        metrics = PipelineMetrics("SAP")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    queries = [
        "SAP software developer",
        "SAP software engineer",
        "SAP intern",
        "SAP cloud developer",
        "SAP ABAP developer",
        "SAP data engineer"
    ]

    seen_ids = set()

    for q in queries:
        start = 0
        while start < 40:
            url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={quote_plus(q)}&location=India&start={start}"
            try:
                res = requests.get(url, headers=headers, timeout=15)
                if res.status_code != 200 or not res.text.strip():
                    break

                soup = BeautifulSoup(res.text, "html.parser")
                cards = soup.find_all("li")
                if not cards:
                    break

                raw_jobs = []
                for c in cards:
                    try:
                        title_el = c.find("h3", class_="base-search-card__title")
                        comp_el = c.find("h4", class_="base-search-card__subtitle")
                        loc_el = c.find("span", class_="job-search-card__location")
                        link_el = c.find("a", class_="base-card__full-link")

                        if not title_el or not link_el:
                            continue

                        company_text = comp_el.get_text(strip=True) if comp_el else ""
                        if "sap" not in company_text.lower():
                            continue

                        title = title_el.get_text(strip=True)
                        href = link_el.get("href", "").split("?")[0]
                        location = loc_el.get_text(strip=True) if loc_el else "India"

                        job_id_part = href.rstrip("/").split("-")[-1]
                        if not job_id_part or job_id_part in seen_ids:
                            continue
                        seen_ids.add(job_id_part)

                        is_early_career = any(
                            kw in title.lower()
                            for kw in ["intern", "graduate", "entry level", "fresher", "associate", "trainee"]
                        )

                        raw_jobs.append({
                            "job_id": f"sap-{job_id_part}",
                            "company": "SAP",
                            "title": title,
                            "location": location,
                            "country": "India",
                            "experience_text": "0-1 years" if is_early_career else "",
                            "apply_link": href,
                            "source": "SAP Careers",
                        })
                    except Exception as parse_e:
                        print(f"Error parsing SAP job item: {parse_e}")
                        continue

                if raw_jobs:
                    process_jobs_batch(raw_jobs, metrics)

                start += 10

            except Exception as e:
                print(f"Error fetching SAP jobs for query '{q}': {e}")
                break

    metrics.finish(status="SUCCESS")
    return metrics


if __name__ == "__main__":
    m = scrape_sap()
    print(m.summary_line())
