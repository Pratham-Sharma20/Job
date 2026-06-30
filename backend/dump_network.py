from playwright.sync_api import sync_playwright

def dump_network():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        def handle_request(request):
            if "api" in request.url or "search" in request.url or "graphql" in request.url:
                print(f"Request: {request.url}")
        
        def handle_response(response):
            if "api" in response.url or "search" in response.url or "graphql" in response.url:
                print(f"Response: {response.url} - {response.status}")
                if "search" in response.url and "json" in response.headers.get("content-type", ""):
                    try:
                        print("JSON Data:", response.json()[:200])
                    except:
                        pass
                        
        page.on("request", handle_request)
        page.on("response", handle_response)
        
        print("Navigating...")
        page.goto('https://jobs.apple.com/en-in/search?search=software%20engineer%20intern&location=india-INDC', wait_until='networkidle')
        page.wait_for_timeout(3000)
        browser.close()

dump_network()
