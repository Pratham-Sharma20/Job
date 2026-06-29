from playwright.sync_api import sync_playwright
import json

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        def handle_response(response):
            if "api" in response.url and "eightfold" not in response.url:
                print(f"[{response.status}] {response.url}")
                try:
                    data = response.text()
                    if "job" in data.lower():
                        print(data[:200])
                except Exception as e:
                    # Some responses (binary, streaming) can't be read as text
                    print(f"  [Could not read response body: {e}]")

        page.on("response", handle_response)
        print("Navigating to Microsoft Careers...")
        page.goto(
            "https://jobs.careers.microsoft.com/global/en/search"
            "?q=software%20engineer%20intern&l=en_us&pg=1&pgSz=20&o=Relevance&flt=true",
            timeout=60000  # Fixed: add explicit timeout (default 30 s can time out on slow networks)
        )
        page.wait_for_timeout(10000)
        browser.close()

if __name__ == "__main__":
    run()
