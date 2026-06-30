import requests
import json
import time
from datetime import datetime
from db import jobs_collection

def extract_json_object(text, start_index):
    """Extracts a JSON object from text starting at start_index by matching braces."""
    stack = []
    in_string = False
    escape = False
    
    for i in range(start_index, len(text)):
        char = text[i]
        
        if not in_string:
            if char == '{':
                stack.append('{')
            elif char == '}':
                if not stack:
                    return None
                stack.pop()
                if not stack:
                    return text[start_index:i+1]
            elif char == '"':
                in_string = True
        else:
            if escape:
                escape = False
            elif char == '\\':
                escape = True
            elif char == '"':
                in_string = False
                
    return None

def save_to_database(jobs):
    if not jobs:
        print("No jobs to save.")
        return

    saved_count = 0

    for job in jobs:
        unique_id = job.get("jobId", "")
        if not unique_id:
            unique_id = job.get("jobSeqNo", "")
            
        if not unique_id:
            unique_id = f"Adobe-{job.get('title', '')}-{job.get('cityStateCountry', '')}"
            
        formatted_job = {
            "job_id": unique_id,
            "title": job.get("title", ""),
            "location": job.get("cityStateCountry", ""),
            "posted_date": job.get("postedDate", ""),
            "work_site": "On-site/Hybrid", # Adobe uses locations mostly
            "profession": job.get("category", ""),
            "discipline": "Engineering and Product",
            "employment_type": job.get("type", job.get("experienceLevel", "Full time")),
            "apply_link": job.get("applyUrl", ""),
            "description": job.get("descriptionTeaser", ""),
            "company": "Adobe",
            "source": "Adobe Careers",
            "scraped_at": datetime.now().isoformat(timespec="seconds"),
        }

        jobs_collection.update_one(
            {
                "company": "Adobe",
                "job_id": unique_id,
            },
            {
                "$set": formatted_job,
            },
            upsert=True,
        )

        saved_count += 1

    print(f"Successfully saved {saved_count} jobs to the database.")

def scrape_adobe_jobs():
    base_url = 'https://careers.adobe.com/us/en/c/engineering-and-product-jobs'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
    }
    
    all_india_jobs = []
    offset = 0
    total_hits = None
    
    print(f"Starting to scrape all pages from {base_url}...")
    
    while True:
        url = base_url if offset == 0 else f"{base_url}?from={offset}&s=1"
        print(f"Fetching offset {offset}...")
        
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Failed to fetch page, status code: {response.status_code}")
            break

        search_str = "phApp.ddo = {"
        start_idx = response.text.find(search_str)
        
        if start_idx == -1:
            print("Could not find phApp.ddo in the page source. Stopping.")
            break
            
        start_idx += len("phApp.ddo = ")
        
        json_str = extract_json_object(response.text, start_idx)
        if not json_str:
            print("Failed to extract JSON object. Stopping.")
            break
            
        try:
            ddo_json = json.loads(json_str)
            refine_search = ddo_json.get('eagerLoadRefineSearch', {})
            data = refine_search.get('data', {})
            
            if total_hits is None:
                total_hits = refine_search.get('totalHits', 0)
                print(f"Total jobs available (all countries): {total_hits}")
                
            jobs = data.get('jobs', [])
            if not jobs:
                print("No jobs found on this page. Finished.")
                break
                
            india_jobs = [job for job in jobs if job.get('country') == 'India']
            all_india_jobs.extend(india_jobs)
            print(f"Found {len(jobs)} jobs on page, {len(india_jobs)} in India.")
            
            offset += len(jobs)
            
            if offset >= total_hits:
                print("Reached total hits. Finished.")
                break
                
            # Be polite to the server
            time.sleep(0.5)
            
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON: {e}")
            break

    print(f"\nScraping complete! Found a total of {len(all_india_jobs)} jobs in India.")
    
    save_to_database(all_india_jobs)

def scrape_apple_jobs():
    from playwright.sync_api import sync_playwright
    from datetime import datetime
    
    print("Starting to scrape Apple jobs...")
    
    scraped_jobs = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        page_num = 1
        while True:
            url = f"https://jobs.apple.com/en-in/search?search=software%20engineer%20intern&location=india-INDC&page={page_num}"
            print(f"Fetching Apple jobs page {page_num}...")
            page.goto(url, wait_until='networkidle')
            
            try:
                # Wait for job results to load
                page.wait_for_selector('div.job-list-item', timeout=10000)
            except Exception as e:
                # If it times out, we likely hit a page with no results or ran out of pages
                print(f"No more jobs found on page {page_num}.")
                break
                
            rows = page.query_selector_all('div.job-list-item')
            if not rows:
                break
                
            for row in rows:
                title_el = row.query_selector('a.link-inline.t-intro')
                if not title_el:
                    continue
                    
                title = title_el.inner_text().strip()
                link = title_el.get_attribute('href')
                if link and not link.startswith('http'):
                    link = "https://jobs.apple.com" + link
                    
                date_el = row.query_selector('span.job-posted-date')
                posted_date = date_el.inner_text().strip() if date_el else ""
                
                location_el = row.query_selector('span[id^="search-store-name"]')
                if not location_el:
                    location_el = row.query_selector('div.job-title-location span:not(.a11y)')
                location = location_el.inner_text().strip() if location_el else "India"
                
                unique_id = f"Apple-{title}-{location}"
                
                formatted_job = {
                    "job_id": unique_id,
                    "title": title,
                    "location": location,
                    "posted_date": posted_date,
                    "work_site": "On-site/Hybrid",
                    "profession": "Software Engineering",
                    "discipline": "Engineering",
                    "employment_type": "Internship" if "intern" in title.lower() else "Full time",
                    "apply_link": link,
                    "description": "", 
                    "company": "Apple",
                    "source": "Apple Careers",
                    "scraped_at": datetime.now().isoformat(timespec="seconds"),
                }
                scraped_jobs.append(formatted_job)
                
            # If less than 20 rows were found, we are on the last page
            if len(rows) < 20:
                print(f"Reached the last page ({page_num}) for Apple jobs.")
                break
                
            page_num += 1
            
        browser.close()
        
    if scraped_jobs:
        from db import jobs_collection
        saved_count = 0
        for job in scraped_jobs:
            jobs_collection.update_one(
                {
                    "company": "Apple",
                    "job_id": job["job_id"],
                },
                {
                    "$set": job,
                },
                upsert=True,
            )
            saved_count += 1
        print(f"Successfully saved {saved_count} Apple jobs to the database.")
    else:
        print("No Apple jobs found.")

if __name__ == '__main__':
    scrape_adobe_jobs()
    scrape_apple_jobs()
