from playwright.sync_api import sync_playwright

def test_apple():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto('https://jobs.apple.com/en-in/search?search=software%20engineer%20intern&location=india-INDC', wait_until='networkidle')
        page.wait_for_timeout(5000)
        with open('apple_dom.html', 'w', encoding='utf-8') as f:
            f.write(page.content())
        browser.close()

test_apple()
