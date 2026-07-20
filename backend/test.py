import requests
from urllib.parse import quote_plus
from datetime import datetime
from db import jobs_collection
from notifier import send_telegram_notification

keywords = [
    "intern", "internship", "new grad", "graduate",
    "fresher", "entry level", "software engineer",
    "sde", "sde i"
]

def is_early(title):
    title = title.lower()
    return any(k in title for k in keywords)

def save_job(company, title, location, link, source):
    if not title or not link:
        return

    # Use link as job_id because job URLs on Greenhouse/Lever/Workday/Amazon are strictly unique per position
    job_id = link

    job = {
        "job_id": job_id,
        "company": company,
        "title": title,
        "location": location,
        "apply_link": link,
        "posted_date": "",
        "work_site": "",
        "profession": "",
        "discipline": "",
        "employment_type": "",
        "description": "",
        "source": source,
        "scraped_at": datetime.now().isoformat(timespec="seconds"),
    }

    result = jobs_collection.update_one(
        {"company": company, "job_id": job_id},
        {"$set": job},
        upsert=True,
    )

    if result.upserted_id is not None:
        send_telegram_notification(job)

def scrape_amazon():
    queries = [
        "software development engineer intern",
        "sde intern",
        "software development engineer new grad",
        "sde i"
    ]

    for q in queries:
        url = (
            "https://www.amazon.jobs/en/search.json?"
            f"base_query={quote_plus(q)}&loc_query=India&result_limit=100&offset=0"
        )

        try:
            res = requests.get(url, timeout=20)
            res.raise_for_status()  # Fixed: raise on HTTP errors instead of silently continuing
            data = res.json()

            for job in data.get("jobs", []):
                title = job.get("title", "")
                location = job.get("normalized_location", "")
                job_path = job.get("job_path", "")
                # Avoid double slashes if job_path doesn't start with "/"
                if job_path and not job_path.startswith("/"):
                    job_path = "/" + job_path
                link = "https://www.amazon.jobs" + job_path

                if is_early(title):
                    save_job("Amazon", title, location, link, "Amazon API")

        except requests.HTTPError as e:
            print("Amazon HTTP error:", e)
        except requests.RequestException as e:
            print("Amazon request failed:", e)
        except Exception as e:
            print("Amazon failed:", e)

def add_faang_search_links():
    search_pages = {
        "Google": "https://www.google.com/about/careers/applications/jobs/results/?q=software%20engineer%20intern",
        "Microsoft": "https://careers.microsoft.com/v2/global/en/search?q=software%20engineer%20intern",
        "Apple": "https://jobs.apple.com/en-in/search?search=software%20engineer%20intern",
        "Meta": "https://www.metacareers.com/jobs?q=software%20engineer%20intern",
        "Netflix": "https://jobs.netflix.com/search?q=intern",
        "OpenAI": "https://openai.com/careers/search",
        "Adobe": "https://careers.adobe.com/us/en/search-results?keywords=software%20engineer%20intern",
    }

    for company, link in search_pages.items():
        save_job(
            company,
            "Official early-career / internship search page",
            "Global",
            link,
            "Official Careers Search Link"
        )

def scrape_greenhouse(company, board):
    url = f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs"

    try:
        res = requests.get(url, timeout=20)
        res.raise_for_status()  # Fixed: raise on HTTP errors
        data = res.json()

        for job in data.get("jobs", []):
            title = job.get("title", "")
            location = job.get("location", {}).get("name", "")
            link = job.get("absolute_url", "")

            if is_early(title):
                save_job(company, title, location, link, "Greenhouse")

    except requests.HTTPError as e:
        print(f"{company} Greenhouse HTTP error:", e)
    except Exception as e:
        print(f"{company} failed:", e)

def scrape_lever(company, board):
    url = f"https://api.lever.co/v0/postings/{board}?mode=json"

    try:
        res = requests.get(url, timeout=20)
        res.raise_for_status()  # Fixed: raise on HTTP errors
        data = res.json()

        # Lever returns a list of postings
        if not isinstance(data, list):
            print(f"{company} Lever: unexpected response format")
            return

        for job in data:
            categories = job.get("categories", {})

            if not isinstance(categories, dict):
                categories = {}

            title = job.get("text", "")
            location = categories.get("location", "")
            link = job.get("hostedUrl", "")

            if is_early(title):
                save_job(company, title, location, link, "Lever")

    except requests.HTTPError as e:
        print(f"{company} Lever HTTP error:", e)
    except Exception as e:
        print(f"{company} failed:", e)

def scrape_workday(company, host, tenant, site):
    """
    Workday's public jobs API endpoint.
    The job detail link is built as: {host}/{site}{externalPath}
    externalPath always starts with '/', so no extra slash is needed.
    """
    url = f"{host}/wday/cxs/{tenant}/{site}/jobs"
    payload = {
        "appliedFacets": {},
        "limit": 100,
        "offset": 0,
        "searchText": ""
    }
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    try:
        res = requests.post(url, json=payload, headers=headers, timeout=20)
        res.raise_for_status()  # Fixed: raise on HTTP errors
        data = res.json()

        for job in data.get("jobPostings", []):
            title = job.get("title", "")
            location = job.get("locationsText", "")
            external_path = job.get("externalPath", "")
            # externalPath starts with '/' — build link correctly
            link = f"{host}/{site}{external_path}"

            if is_early(title):
                save_job(company, title, location, link, "Workday")

    except requests.HTTPError as e:
        print(f"{company} Workday HTTP error:", e)
    except Exception as e:
        print(f"{company} failed:", e)


boards = {
    "Anthropic":    ("greenhouse", "anthropic"),
    "Databricks":   ("greenhouse", "databricks"),
    "Rubrik":       ("greenhouse", "rubrik"),
    "Postman":      ("greenhouse", "postman"),
    "BrowserStack": ("greenhouse", "browserstack"),
    "Cohesity":     ("greenhouse", "cohesity"),
    "Nutanix":      ("greenhouse", "nutanix"),
    "Meesho":       ("greenhouse", "meesho"),
    "Razorpay":     ("greenhouse", "razorpay"),
    "Atlassian":    ("lever", "atlassian"),
    "Airbnb":       ("lever", "airbnb"),
}


# Fixed: wrapped in __main__ guard so this file can be safely imported
# without triggering all scraping (e.g. from tests or other modules).
if __name__ == "__main__":
    print("Scraping Amazon...")
    scrape_amazon()

    print("Adding official search links for complex portals (Google, Microsoft, Meta, Apple, Netflix, OpenAI)...")
    add_faang_search_links()

    print("Scraping Nvidia (Workday)...")
    scrape_workday("Nvidia", "https://nvidia.wd5.myworkdayjobs.com", "nvidia", "NVIDIAExternalCareerSite")

    for company, (platform, board) in boards.items():
        print(f"Scraping {company}...")
        if platform == "greenhouse":
            scrape_greenhouse(company, board)
        else:
            scrape_lever(company, board)

    print("Done. Jobs saved to MongoDB.")
    print("Total jobs in database:", jobs_collection.count_documents({}))