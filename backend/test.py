"""
Master Job Scraping Runner for India Early-Career Tech Roles.
Executes ATS adapters (Greenhouse, Lever, Workday) and custom company scrapers
through the centralized pipeline and filtering engine.
"""

import requests
from urllib.parse import quote_plus
from typing import List, Optional
from db import jobs_collection
from pipeline import process_single_job, process_jobs_batch, PipelineMetrics
from companies import COMPANIES
from adapters.greenhouse import scrape_greenhouse_board
from adapters.lever import scrape_lever_board
from adapters.workday import scrape_workday_instance

# Import custom scrapers
from scrapers.flipkart import scrape_flipkart
from scrapers.swiggy import scrape_swiggy
from scrapers.phonepe import scrape_phonepe
from scrapers.zepto import scrape_zepto
from scrapers.myntra import scrape_myntra
from scrapers.juspay import scrape_juspay
from scrapers.eternal import scrape_eternal
from scrapers.meta import scrape_meta
from scrapers.amd import scrape_amd
from scrapers.qualcomm import scrape_qualcomm
from scrapers.oracle import scrape_oracle
from scrapers.cisco import scrape_cisco
from scrapers.atlassian import scrape_atlassian
from scrapers.uber import scrape_uber
from scrapers.linkedin import scrape_linkedin
from scrapers.servicenow import scrape_servicenow
from scrapers.intuit import scrape_intuit
from scrapers.netflix import scrape_netflix
from scrapers.snowflake import scrape_snowflake
from scrapers.sap import scrape_sap
from scrapers.micron import scrape_micron
from scrapers.paypal import scrape_paypal
from scrapers.zoom import scrape_zoom


def scrape_amazon(metrics: Optional[PipelineMetrics] = None):
    """Scrapes Amazon Jobs API strictly for early-career India SDE/SWE roles."""
    if metrics is None:
        metrics = PipelineMetrics("Amazon")

    queries = [
        "software development engineer intern",
        "sde intern",
        "software development engineer new grad",
        "sde i",
    ]

    for q in queries:
        url = (
            "https://www.amazon.jobs/en/search.json?"
            f"base_query={quote_plus(q)}&loc_query=India&country=IND&result_limit=100&offset=0"
        )

        try:
            res = requests.get(url, timeout=20)
            res.raise_for_status()
            data = res.json()

            raw_jobs = []
            for job in data.get("jobs", []):
                job_path = job.get("job_path", "")
                if job_path and not job_path.startswith("/"):
                    job_path = "/" + job_path
                link = "https://www.amazon.jobs" + job_path if job_path else ""

                title = job.get("title", "")
                normalized_location = str(job.get("normalized_location") or job.get("location") or "India")

                raw_jobs.append({
                    "job_id": link or f"amazon-{job.get('id_icims')}",
                    "company": "Amazon",
                    "title": title,
                    "location": normalized_location,
                    "country": "India",
                    "experience_text": "0-1 years" if any(w in title.lower() for w in ["intern", "new grad", "sde i", "sde 1"]) else "",
                    "apply_link": link,
                    "posted_date": job.get("posted_date", ""),
                    "description": job.get("description_short", ""),
                    "source": "Amazon API",
                })

            process_jobs_batch(raw_jobs, metrics)

        except Exception as e:
            print(f"Amazon fetch query '{q}' failed: {e}")

    metrics.finish(status="SUCCESS")
    return metrics


def run_all_scrapers() -> List[PipelineMetrics]:
    """Runs all configured ATS adapters and custom company scrapers with failure isolation."""
    metrics_list: List[PipelineMetrics] = []

    print("\n" + "=" * 70)
    print("STARTING COMPREHENSIVE SDE/INTERN JOB SCRAPING (INDIA)")
    print("=" * 70 + "\n")

    # 1. Custom Company Scrapers
    custom_scrapers = [
        ("Flipkart", scrape_flipkart),
        ("Swiggy", scrape_swiggy),
        ("PhonePe", scrape_phonepe),
        ("Zepto", scrape_zepto),
        ("Myntra", scrape_myntra),
        ("Juspay", scrape_juspay),
        ("Eternal", scrape_eternal),
        ("Amazon", scrape_amazon),
        ("Meta", scrape_meta),
        ("AMD", scrape_amd),
        ("Qualcomm", scrape_qualcomm),
        ("Oracle", scrape_oracle),
        ("Cisco", scrape_cisco),
        ("Atlassian", scrape_atlassian),
        ("Uber", scrape_uber),
        ("LinkedIn", scrape_linkedin),
        ("ServiceNow", scrape_servicenow),
        ("Intuit", scrape_intuit),
        ("Netflix", scrape_netflix),
        ("Snowflake", scrape_snowflake),
        ("SAP", scrape_sap),
        ("Micron", scrape_micron),
        ("PayPal", scrape_paypal),
        ("Zoom", scrape_zoom),
    ]

    for name, scraper_fn in custom_scrapers:
        m = PipelineMetrics(name)
        try:
            scraper_fn(m)
        except Exception as e:
            m.finish(status="ERROR", error_message=str(e))
            print(f"Scraper {name} encountered fatal error: {e}")
        metrics_list.append(m)
        print(m.summary_line())

    # 2. ATS Configured Companies (Greenhouse, Lever, Workday)
    for company, config in COMPANIES.items():
        provider = config.get("provider")
        m = PipelineMetrics(f"{company} ({provider.capitalize()})")

        try:
            if provider == "greenhouse":
                scrape_greenhouse_board(
                    company, config["board"], m,
                    india_only=config.get("india_only", False)
                )
            elif provider == "lever":
                scrape_lever_board(company, config["board"], m)
            elif provider == "workday":
                scrape_workday_instance(
                    company=company,
                    host=config["host"],
                    tenant=config["tenant"],
                    site=config["site"],
                    search_queries=config.get("search_queries"),
                    country_facets=config.get("country_facets"),
                    facet_param=config.get("facet_param"),
                    applied_facets=config.get("applied_facets"),
                    metrics=m
                )
        except Exception as e:
            m.finish(status="ERROR", error_message=str(e))
            print(f"ATS {company} encountered fatal error: {e}")

        metrics_list.append(m)
        print(m.summary_line())

    # Execution Report Summary Table
    print("\n" + "=" * 75)
    print(f"{'Company / Source':<25} {'Status':<8} {'Fetched':>8} {'Qualified':>11} {'New':>6} {'Duration':>10}")
    print("-" * 75)
    total_fetched = sum(m.fetched for m in metrics_list)
    total_qualified = sum(m.qualified for m in metrics_list)
    total_new = sum(m.new_jobs for m in metrics_list)

    for m in metrics_list:
        status_str = "OK" if m.status == "SUCCESS" else "FAIL"
        print(f"{m.scraper_name:<25} {status_str:<8} {m.fetched:>8} {m.qualified:>11} {m.new_jobs:>6} {m.duration_seconds:>9}s")

    print("-" * 75)
    print(f"{'TOTAL':<25} {'':<8} {total_fetched:>8} {total_qualified:>11} {total_new:>6}")
    print("=" * 75 + "\n")
    print(f"Total jobs stored in MongoDB: {jobs_collection.count_documents({})}")

    return metrics_list


if __name__ == "__main__":
    run_all_scrapers()