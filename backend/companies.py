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
    },
    "Salesforce": {
        "provider": "workday",
        "host": "https://salesforce.wd12.myworkdayjobs.com",
        "tenant": "salesforce",
        "site": "External_Career_Site",
        "facet_param": "CF_-_REC_-_LRV_-_Job_Posting_Anchor_-_Country_from_Job_Posting_Location_Extended",
        "country_facets": ["c4f78be1a8f14da0ab49ce1162348a5e"],  # India country facet in Salesforce Workday
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
    },
    "Stripe": {
        "provider": "greenhouse",
        "board": "stripe",
        "india_only": True,
    },
    "Databricks": {
        "provider": "greenhouse",
        "board": "databricks",
        "india_only": True,
    },
    "Intel": {
        "provider": "workday",
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
    },
    "Workday": {
        "provider": "workday",
        "host": "https://workday.wd5.myworkdayjobs.com",
        "tenant": "workday",
        "site": "Workday",
        "facet_param": "Location_Country",
        "country_facets": ["c4f78be1a8f14da0ab49ce1162348a5e"],  # India country facet in Workday
        "search_queries": [
            "software engineer",
            "software development engineer",
            "intern",
            "backend",
            "frontend",
            "full stack",
            "developer",
            "associate"
        ]
    },
    "Twilio": {
        "provider": "greenhouse",
        "board": "twilio",
        "india_only": True,
    },
    "Visa": {
        "provider": "workday",
        "host": "https://visa.wd5.myworkdayjobs.com",
        "tenant": "visa",
        "site": "Visa",
        "search_queries": [
            "software engineer",
            "software development engineer",
            "intern",
            "backend",
            "frontend",
            "full stack",
            "developer",
            "data engineer",
            "ai engineer",
            "associate"
        ]
    },
    "Mastercard": {
        "provider": "workday",
        "host": "https://mastercard.wd1.myworkdayjobs.com",
        "tenant": "mastercard",
        "site": "CorporateCareers",
        "search_queries": [
            "software engineer",
            "software development engineer",
            "intern",
            "backend",
            "frontend",
            "full stack",
            "developer",
            "data engineer",
            "ai engineer",
            "associate"
        ]
    }
}

