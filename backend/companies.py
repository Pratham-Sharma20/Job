"""
Company ATS and target configurations.
Allows decoupling board IDs and provider endpoints from scraper logic.
"""

COMPANIES = {
    # Greenhouse boards (Active & Verified)
    "Groww": {
        "provider": "greenhouse",
        "board": "groww",
    },
    "Rubrik": {
        "provider": "greenhouse",
        "board": "rubrik",
        "india_only": True,   # Global board — pre-filter to India offices only
    },
    "Postman": {
        "provider": "greenhouse",
        "board": "postman",
        "india_only": True,   # Global board — pre-filter to India offices only
    },

    # Lever boards (Active & Verified)
    "CRED": {
        "provider": "lever",
        "board": "cred",
    },

    # Workday portals (Active & Verified)
    "Walmart": {
        "provider": "workday",
        "host": "https://walmart.wd504.myworkdayjobs.com",
        "tenant": "walmart",
        "site": "WalmartExternal",
        "country_facets": ["bc33aa3152ec42d4995f4791a106ed09"],  # India country facet in Walmart Workday
        "search_queries": [
            "software engineer",
            "software development engineer",
            "backend",
            "frontend",
            "full stack"
        ]
    },
    "Nvidia": {
        "provider": "workday",
        "host": "https://nvidia.wd5.myworkdayjobs.com",
        "tenant": "nvidia",
        "site": "NVIDIAExternalCareerSite",
        "country_facets": [],
        "search_queries": ["software engineer", "intern"]
    }
}
