"""
Salesforce Careers Scraper.
Scrapes Salesforce Career Portal (https://careers.salesforce.com/en/jobs/)
powered by Salesforce Workday CXS endpoints.
"""

import os
import sys
from typing import Optional

# Ensure backend root is on sys.path
backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from pipeline import PipelineMetrics
from adapters.workday import scrape_workday_instance

SALESFORCE_CONFIG = {
    "host": "https://salesforce.wd12.myworkdayjobs.com",
    "tenant": "salesforce",
    "site": "External_Career_Site",
    "facet_param": "CF_-_REC_-_LRV_-_Job_Posting_Anchor_-_Country_from_Job_Posting_Location_Extended",
    "country_facets": ["c4f78be1a8f14da0ab49ce1162348a5e"],  # India facet
    "search_queries": [
        "software engineer",
        "software development engineer",
        "intern",
        "backend",
        "frontend",
        "full stack",
        "developer",
        "member of technical staff",
        "associate"
    ]
}


def scrape_salesforce(metrics: Optional[PipelineMetrics] = None) -> PipelineMetrics:
    """Scrapes Salesforce careers for early-career and tech opportunities in India."""
    if metrics is None:
        metrics = PipelineMetrics("Salesforce")

    return scrape_workday_instance(
        company="Salesforce",
        host=SALESFORCE_CONFIG["host"],
        tenant=SALESFORCE_CONFIG["tenant"],
        site=SALESFORCE_CONFIG["site"],
        facet_param=SALESFORCE_CONFIG["facet_param"],
        country_facets=SALESFORCE_CONFIG["country_facets"],
        search_queries=SALESFORCE_CONFIG["search_queries"],
        metrics=metrics
    )


if __name__ == "__main__":
    m = scrape_salesforce()
    print(m.summary_line())
