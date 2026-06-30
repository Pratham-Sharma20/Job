from playwright.sync_api import sync_playwright

def screenshot_apple():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto('https://jobs.apple.com/en-in/search?search=software%20engineer%20intern&location=india-INDC', wait_until='networkidle')
        page.wait_for_timeout(3000)
        page.screenshot(path='apple_screenshot.png')
        browser.close()

screenshot_apple()
