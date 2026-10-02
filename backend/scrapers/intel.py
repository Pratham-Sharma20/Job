"""
Intel Careers Scraper.
Scrapes Intel Workday ATS (https://jobs.intel.com / https://intel.wd1.myworkdayjobs.com/External)
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

INTEL_CONFIG = {
    "host": "https://intel.wd1.myworkdayjobs.com",
    "tenant": "intel",
    "site": "External",
    "search_queries": [
        "software engineer India",
        "software development engineer India",
        "intern India",
        "graduate intern India",
        "backend India",
        "frontend India",
        "system software India",
        "firmware India",
        "cloud India"
    ]
}


def scrape_intel(metrics: Optional[PipelineMetrics] = None) -> PipelineMetrics:
    """Scrapes Intel careers for early-career and tech opportunities in India."""
    if metrics is None:
        metrics = PipelineMetrics("Intel")

    return scrape_workday_instance(
        company="Intel",
        host=INTEL_CONFIG["host"],
        tenant=INTEL_CONFIG["tenant"],
        site=INTEL_CONFIG["site"],
        search_queries=INTEL_CONFIG["search_queries"],
        metrics=metrics
    )


if __name__ == "__main__":
    m = scrape_intel()
    print(m.summary_line())
