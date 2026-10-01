"""
Workday ATS Adapter.
Fetches jobs from Workday public CXS endpoints (Walmart, Nvidia, etc.) and forwards to pipeline.
"""

import requests
from typing import Optional, List, Dict, Any
from pipeline import process_jobs_batch, PipelineMetrics

def scrape_workday_instance(
    company: str,
    host: str,
    tenant: str,
    site: str,
    search_queries: Optional[List[str]] = None,
    country_facets: Optional[List[str]] = None,
    metrics: Optional[PipelineMetrics] = None
):
    """Scrapes a Workday career instance and forwards raw jobs to pipeline."""
    if metrics is None:
        metrics = PipelineMetrics(f"{company} (Workday)")

    url = f"{host}/wday/cxs/{tenant}/{site}/jobs"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    queries = search_queries if search_queries else ["software engineer", "intern"]
    applied_facets: Dict[str, Any] = {}
    if country_facets:
        applied_facets["locationCountry"] = country_facets

    seen_ids = set()

    try:
        for q in queries:
            offset = 0
            limit = 20
            while offset < 100:  # Cap at top 100 jobs per query for speed and rate limits
                payload = {
                    "appliedFacets": applied_facets,
                    "limit": limit,
                    "offset": offset,
                    "searchText": q
                }

                try:
                    res = requests.post(url, json=payload, headers=headers, timeout=20)
                    if res.status_code != 200:
                        break

                    data = res.json()
                    job_postings = data.get("jobPostings", [])
                    if not job_postings:
                        break

                    raw_jobs = []
                    for job in job_postings:
                        external_path = job.get("externalPath", "")
                        bullet_fields = job.get("bulletFields", [])
                        job_id = external_path or job.get("bulletFields", [""])[0] if bullet_fields else ""
                        
                        if job_id in seen_ids:
                            continue
                        seen_ids.add(job_id)

                        link = f"{host}/{site}{external_path}"
                        title = job.get("title", "")
                        location = job.get("locationsText", "")

                        raw_jobs.append({
                            "job_id": str(job_id or link),
                            "company": company,
                            "title": title,
                            "location": location,
                            "country": "India" if country_facets else "",
                            "apply_link": link,
                            "posted_date": job.get("postedOn", ""),
                            "source": "Workday",
                        })

                    process_jobs_batch(raw_jobs, metrics)

                    offset += limit
                    total = data.get("total", 0)
                    if offset >= total:
                        break

                except Exception as inner_e:
                    print(f"Workday page fetch failed for {company} query '{q}': {inner_e}")
                    break

        metrics.finish(status="SUCCESS")

    except Exception as e:
        metrics.finish(status="ERROR", error_message=str(e))
        print(f"Error scraping Workday for {company}: {e}")

    return metrics
