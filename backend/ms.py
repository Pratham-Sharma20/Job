import requests
import time
import json
import re
from datetime import datetime
from urllib.parse import urljoin
from db import jobs_collection

BASE_URL = "https://apply.careers.microsoft.com/api/pcsx/search"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
}

LOCATIONS = [
    "India",
    "Bangalore, India",
    "Bengaluru, India",
    "Hyderabad, India",
    "Noida, India",
    "Gurugram, India",
    "Gurgaon, India",
    "Mumbai, India",
    "Pune, India",
    "New Delhi, India",
]

SOFTWARE_KEYWORDS = [
    "software engineer",
    "software engineering",
    "software development engineer",
    "sde",
    "developer",
    "frontend",
    "backend",
    "full stack",
    "fullstack",
    "cloud engineer",
    "platform engineer",
    "data engineer",
    "machine learning",
    "ai engineer",
    "research software",
    "apps full stack engineer",
]

EARLY_KEYWORDS = [
    "intern",
    "internship",
    "graduate",
    "new grad",
    "early career",
    "student",
    "university",
    "fresher",
]

EXCLUDE_KEYWORDS = [
    "senior",
    "principal",
    "staff",
    "lead",
    "manager",
    "director",
    "architect",
    "5+ years",
    "7+ years",
    "10+ years",
]

SAVE_FILTERED_ONLY = True
# True  = save only software / early-career jobs
# False = save all Microsoft India jobs


def contains_phrase(text, keyword):
    text = text.lower()
    keyword = keyword.lower()

    pattern = r"\b" + re.escape(keyword) + r"\b"
    return re.search(pattern, text) is not None


def contains_any(text, keywords):
    return any(contains_phrase(text, keyword) for keyword in keywords)


def find_value(obj, possible_keys):
    possible_keys = [key.lower() for key in possible_keys]

    if isinstance(obj, dict):
        for key, value in obj.items():
            if key.lower() in possible_keys and value not in [None, "", []]:
                return value

        for value in obj.values():
            result = find_value(value, possible_keys)
            if result not in [None, "", []]:
                return result

    elif isinstance(obj, list):
        for item in obj:
            result = find_value(item, possible_keys)
            if result not in [None, "", []]:
                return result

    return None


def value_to_text(value):
    if value is None:
        return ""

    if isinstance(value, str):
        return value.strip()

    if isinstance(value, (int, float)):
        return str(value)

    if isinstance(value, list):
        return " | ".join(value_to_text(item) for item in value if item)

    if isinstance(value, dict):
        parts = []

        for key in [
            "city",
            "state",
            "region",
            "country",
            "name",
            "displayName",
            "location",
            "address",
        ]:
            if key in value and value[key]:
                parts.append(value_to_text(value[key]))

        if parts:
            return ", ".join(parts)

        return json.dumps(value, ensure_ascii=False)

    return str(value)


def extract_positions(data):
    if isinstance(data, dict):
        if "data" in data and isinstance(data["data"], dict):
            if "positions" in data["data"]:
                return data["data"]["positions"]

            if "jobs" in data["data"]:
                return data["data"]["jobs"]

        if "positions" in data:
            return data["positions"]

        if "jobs" in data:
            return data["jobs"]

    return []


def clean_job(raw_job):
    job_id = find_value(raw_job, [
        "job_id",
        "jobId",
        "id",
        "position_id",
        "positionId",
        "display_job_id",
        "externalJobId",
        "requisitionId",
        "requisition_id",
    ])

    title = find_value(raw_job, [
        "title",
        "name",
        "jobTitle",
        "positionTitle",
    ])

    location = find_value(raw_job, [
        "location",
        "locations",
        "location_text",
        "primaryLocation",
        "jobLocation",
        "jobLocations",
    ])

    posted_date = find_value(raw_job, [
        "posted_date",
        "postedDate",
        "datePosted",
        "createdDate",
        "posted_ts",
        "postingDate",
        "updated_time",
    ])

    work_site = find_value(raw_job, [
        "work_site",
        "workSite",
        "worksite",
        "workLocationType",
        "efcustom_text_work_site",
    ])

    profession = find_value(raw_job, [
        "profession",
        "jobFamily",
        "efcustom_text_current_profession",
    ])

    discipline = find_value(raw_job, [
        "discipline",
        "efcustom_text_ta_discipline_name",
    ])

    employment_type = find_value(raw_job, [
        "employment_type",
        "employmentType",
        "efcustom_text_employment_type",
    ])

    description = find_value(raw_job, [
        "description",
        "job_description",
        "jobDescription",
        "overview",
    ])

    apply_link = find_value(raw_job, [
        "canonicalPositionUrl",
        "positionUrl",
        "position_url",
        "url",
        "jobUrl",
        "applyLink",
        "externalApplyUrl",
    ])

    job_id = value_to_text(job_id)
    title = value_to_text(title)
    location = value_to_text(location)
    posted_date = value_to_text(posted_date)
    work_site = value_to_text(work_site)
    profession = value_to_text(profession)
    discipline = value_to_text(discipline)
    employment_type = value_to_text(employment_type)
    description = value_to_text(description)
    apply_link = value_to_text(apply_link)

    if apply_link.startswith("/"):
        apply_link = urljoin("https://apply.careers.microsoft.com", apply_link)

    if not apply_link and job_id:
        apply_link = f"https://apply.careers.microsoft.com/careers/job/{job_id}"

    return {
        "job_id": job_id,
        "title": title,
        "location": location,
        "posted_date": posted_date,
        "work_site": work_site,
        "profession": profession,
        "discipline": discipline,
        "employment_type": employment_type,
        "apply_link": apply_link,
        "description": description,
        "company": "Microsoft",
        "source": "Microsoft Careers",
        "scraped_at": datetime.now().isoformat(timespec="seconds"),
    }


def is_software_or_early_job(job):
    title = job.get("title", "").lower()
    profession = job.get("profession", "").lower()
    discipline = job.get("discipline", "").lower()
    employment_type = job.get("employment_type", "").lower()

    main_text = " ".join([
        title,
        profession,
        discipline,
        employment_type,
    ])

    # Important fix:
    # Exclude only by title, not description.
    # Otherwise normal jobs get rejected because descriptions contain words like manager/lead.
    if contains_any(title, EXCLUDE_KEYWORDS):
        return False

    software_match = contains_any(main_text, SOFTWARE_KEYWORDS)
    early_match = contains_any(main_text, EARLY_KEYWORDS)

    return software_match or early_match


def request_with_retry(params, retries=4):
    for attempt in range(retries):
        try:
            response = requests.get(
                BASE_URL,
                headers=HEADERS,
                params=params,
                timeout=20,
            )
        except requests.RequestException as error:
            print("Request error:", error)
            time.sleep(5)
            continue

        if response.status_code == 200:
            return response

        if response.status_code == 429:
            wait_time = 10 * (attempt + 1)
            print(f"Rate limited. Waiting {wait_time} seconds...")
            time.sleep(wait_time)
            continue

        print("Request failed:", response.status_code)
        print(response.text[:300])
        return None

    return None


def scrape_jobs_for_location(location_name):
    jobs = []
    start = 0
    limit = 20

    while True:
        params = {
            "domain": "microsoft.com",
            "query": "",
            "location": location_name,
            "start": start,
            "num": limit,
        }

        response = request_with_retry(params)

        if response is None:
            break

        data = response.json()
        positions = extract_positions(data)

        if not positions:
            break

        print(
            f"Location: {location_name} | start={start} | jobs on page={len(positions)}"
        )

        for raw_job in positions:
            job = clean_job(raw_job)
            jobs.append(job)

        start += limit
        time.sleep(1.5)

    return jobs


def scrape_all_india_jobs():
    all_jobs = []
    seen = set()

    for location in LOCATIONS:
        location_jobs = scrape_jobs_for_location(location)

        for job in location_jobs:
            unique_key = job["job_id"]

            if not unique_key:
                unique_key = f"{job['company']}-{job['title']}-{job['location']}-{job['apply_link']}"

            if unique_key not in seen:
                seen.add(unique_key)
                all_jobs.append(job)

        print(f"Total unique jobs after {location}: {len(all_jobs)}")
        time.sleep(3)

    return all_jobs


def save_to_database(jobs):
    if not jobs:
        print("No jobs to save.")
        return

    saved_count = 0

    for job in jobs:
        unique_id = job.get("job_id", "")

        if not unique_id:
            unique_id = f"{job['company']}-{job['title']}-{job['location']}-{job['apply_link']}"
            job["job_id"] = unique_id

        jobs_collection.update_one(
            {
                "company": job["company"],
                "job_id": unique_id,
            },
            {
                "$set": job,
            },
            upsert=True,
        )

        saved_count += 1

    print(f"Successfully saved {saved_count} jobs to the database.")


def debug_filtering(all_jobs):
    passed = 0
    rejected = 0

    print("\nFiltering debug:")
    print("-" * 80)

    for job in all_jobs:
        if is_software_or_early_job(job):
            passed += 1
        else:
            rejected += 1
            print(
                "REJECTED:",
                job["title"],
                "| Profession:",
                job["profession"],
                "| Discipline:",
                job["discipline"],
            )

    print("-" * 80)
    print("Passed filter:", passed)
    print("Rejected by filter:", rejected)


all_jobs = scrape_all_india_jobs()

debug_filtering(all_jobs)

filtered_jobs = [
    job for job in all_jobs
    if is_software_or_early_job(job)
]

jobs_to_save = filtered_jobs if SAVE_FILTERED_ONLY else all_jobs

save_to_database(jobs_to_save)

print("\nSummary")
print("-" * 80)
print("Total India jobs scraped:", len(all_jobs))
print("Software / early-career jobs found:", len(filtered_jobs))
print("Jobs saved to database:", len(jobs_to_save))

print("\nSaved jobs:")
for job in jobs_to_save:
    print("-" * 80)
    print("Title:", job["title"])
    print("Location:", job["location"])
    print("Profession:", job["profession"])
    print("Discipline:", job["discipline"])
    print("Posted:", job["posted_date"])
    print("Link:", job["apply_link"])