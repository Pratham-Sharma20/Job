import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import pandas as pd
import re
from datetime import datetime
from db import jobs_collection
from notifier import send_telegram_notification

URL = "https://www.google.com/about/careers/applications/jobs/results?location=India&target_level=INTERN_AND_APPRENTICE&target_level=EARLY&employment_type=INTERN&employment_type=FULL_TIME"
BASE_CAREERS_URL = "https://www.google.com/about/careers/applications/"


def clean_text(text):
    return re.sub(r"\s+", " ", text).strip()


def get_job_card(h3_tag):
    card = h3_tag.find_parent("li")
    return card if card else h3_tag.find_parent()


def extract_company(full_text):
    companies = ["Google", "YouTube", "Fitbit", "DeepMind", "Waymo", "Wing"]

    for company in companies:
        if company in full_text:
            return company

    return "Google"


def extract_location(full_text):
    match = re.search(
        r"(Google|YouTube|Fitbit|DeepMind|Waymo|Wing)\s*\|\s*(.*?)(?=Minimum qualifications|Learn more|share|Copy link|Email a friend|$)",
        full_text,
        re.IGNORECASE,
    )

    if match:
        return clean_text(match.group(2))

    match = re.search(
        r"place\s+(.*?India(?:\s*;\s*.*?India)*(?:\s*;\s*\+\d+\s*more)?)\s+bar_chart",
        full_text,
        re.IGNORECASE,
    )

    if match:
        return clean_text(match.group(1))

    return ""


def extract_level(full_text):
    if "Intern & Apprentice" in full_text:
        return "Intern & Apprentice"

    if re.search(r"\bEarly\b", full_text):
        return "Early"

    return ""


def extract_min_qualifications(full_text):
    match = re.search(
        r"Minimum qualifications\s*(.*?)(?=Preferred qualifications|About the job|Responsibilities|Learn more|share|Copy link|Email a friend|$)",
        full_text,
        re.IGNORECASE,
    )

    if match:
        return clean_text(match.group(1))

    return ""


def get_job_link(card, h3_tag=None, base_url=BASE_CAREERS_URL):
    links = card.find_all("a", href=True)

    # Primary: match job detail URLs with a numeric ID
    for link in links:
        href = link["href"].strip()
        if not href or href == "#":
            continue
        if re.search(r"jobs/results/\d+", href):
            clean_href = href.split("?")[0]
            if clean_href.startswith("http://") or clean_href.startswith("https://"):
                return clean_href
            if clean_href.startswith("/about/careers/applications/"):
                return urljoin("https://www.google.com", clean_href)
            if clean_href.startswith("/"):
                return urljoin("https://www.google.com/about/careers/applications", clean_href)
            return urljoin(base_url, clean_href)

    # Check for any link with aria-label indicating job details (e.g. 'Learn more about...')
    for link in links:
        aria_label = link.get("aria-label", "")
        if "Learn more about" in aria_label:
            clean_href = link["href"].strip().split("?")[0]
            return urljoin(base_url, clean_href)

    # Try the h3's parent <a> tag directly
    if h3_tag:
        parent_a = h3_tag.find_parent("a", href=True)
        if parent_a:
            href = parent_a["href"].strip()
            if href and href != "#":
                clean_href = href.split("?")[0]
                return urljoin(base_url, clean_href)

    # Broader: any careers application link that isn't the search page
    for link in links:
        href = link["href"].strip()
        if ("/careers/applications/" in href or "jobs/results" in href) and href != "#":
            clean_href = href.split("?")[0]
            normalized = clean_href.rstrip("/")
            if normalized.endswith("/results") or normalized.endswith("/jobs"):
                continue
            return urljoin(base_url, clean_href)

    return ""


def scrape_jobs_from_html(html):
    soup = BeautifulSoup(html, "html.parser")
    base_tag = soup.find("base", href=True)
    base_url = base_tag["href"] if base_tag else BASE_CAREERS_URL

    jobs = []

    skip_titles = {
        "Locations",
        "Experience",
        "Skills & qualifications",
        "Degree",
        "Job types",
        "Organizations",
        "Sort by",
        "Search sidebar",
    }

    for h3 in soup.find_all("h3"):
        title = clean_text(h3.get_text(" ", strip=True))

        if not title or title in skip_titles:
            continue

        card = get_job_card(h3)

        if not card:
            continue

        full_text = clean_text(card.get_text(" ", strip=True))

        if "India" not in full_text:
            continue

        if "Minimum qualifications" not in full_text:
            continue

        job = {
            "title": title,
            "company": extract_company(full_text),
            "location": extract_location(full_text),
            "level": extract_level(full_text),
            "minimum_qualifications": extract_min_qualifications(full_text),
            "link": get_job_link(card, h3, base_url),
        }

        jobs.append(job)

    return jobs


async def click_next_page(page):
    selectors = [
        "button:has-text('navigate_next')",
        "button[aria-label*='next' i]",
        "button[aria-label*='Next' i]",
        "a[aria-label*='next' i]",
        "a[aria-label*='Next' i]",
    ]

    for selector in selectors:
        locator = page.locator(selector)

        count = await locator.count()

        if count == 0:
            continue

        next_button = locator.nth(count - 1)

        try:
            if await next_button.is_enabled():
                await next_button.click()
                await page.wait_for_timeout(3000)
                return True
        except Exception:
            continue

    return False


async def scrape_google_jobs_all_pages():
    all_jobs = []
    seen = set()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        await page.goto(URL, wait_until="networkidle", timeout=60000)
        await page.wait_for_timeout(3000)

        page_number = 1

        while True:
            print(f"Scraping page {page_number}...")

            html = await page.content()
            jobs = scrape_jobs_from_html(html)

            print(f"Jobs found on page {page_number}: {len(jobs)}")

            for job in jobs:
                key = (
                    job["title"],
                    job["company"],
                    job["location"],
                )

                if key not in seen:
                    seen.add(key)
                    all_jobs.append(job)

            clicked = await click_next_page(page)

            if not clicked:
                print("No more pages found.")
                break

            page_number += 1

        await browser.close()

    return all_jobs


def save_to_database(jobs):
    if not jobs:
        print("No jobs to save.")
        return

    saved_count = 0
    for job in jobs:
        unique_id = job.get("link", "")
        if not unique_id:
            unique_id = f"{job['company']}-{job['title']}-{job['location']}"
            
        # Standardize structure for MongoDB
        db_job = {
            "job_id": unique_id,
            "title": job["title"],
            "company": job["company"],
            "location": job["location"],
            "level": job["level"],
            "minimum_qualifications": job["minimum_qualifications"],
            "apply_link": job["link"],
            "source": "Google Careers",
            "scraped_at": datetime.now().isoformat(timespec="seconds"),
        }

        fallback_id = f"{job['company']}-{job['title']}-{job['location']}"
        existing = jobs_collection.find_one({
            "source": "Google Careers",
            "$or": [
                {"job_id": unique_id},
                {"job_id": fallback_id},
                {"company": job["company"], "title": job["title"], "location": job["location"]},
            ]
        })

        if existing:
            jobs_collection.update_one(
                {"_id": existing["_id"]},
                {"$set": db_job}
            )
        else:
            jobs_collection.insert_one(db_job)
            send_telegram_notification(db_job)

        saved_count += 1

    print(f"Successfully saved {saved_count} jobs to the database.")


async def main():
    print("Starting Google Jobs Scraper...")
    jobs = await scrape_google_jobs_all_pages()

    # df = pd.DataFrame(jobs)
    # df.to_csv("google_india_early_intern_jobs.csv", index=False, encoding="utf-8")
    
    save_to_database(jobs)

    print("Total jobs scraped:", len(jobs))

    if jobs:
        df = pd.DataFrame(jobs)
        print(df[["title", "company", "location", "level", "link"]])
    else:
        print("No jobs found.")


if __name__ == "__main__":
    # Fix: Wrapping top-level await in asyncio.run() to prevent SyntaxError
    asyncio.run(main())
