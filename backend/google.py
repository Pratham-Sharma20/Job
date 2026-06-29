import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import pandas as pd
import re
from datetime import datetime
from db import jobs_collection

URL = "https://www.google.com/about/careers/applications/jobs/results?location=India&target_level=INTERN_AND_APPRENTICE&target_level=EARLY&employment_type=INTERN&employment_type=FULL_TIME"


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


def get_job_link(card):
    links = card.find_all("a", href=True)

    for link in links:
        href = link["href"]

        if "/about/careers/applications/jobs/results/" in href:
            return urljoin("https://www.google.com", href)

    return ""


def scrape_jobs_from_html(html):
    soup = BeautifulSoup(html, "html.parser")

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
            "link": get_job_link(card),
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
        browser = await p.chromium.launch(headless=False)
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

        jobs_collection.update_one(
            {
                "job_id": unique_id,
                "source": "Google Careers"
            },
            {
                "$set": db_job
            },
            upsert=True,
        )
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
