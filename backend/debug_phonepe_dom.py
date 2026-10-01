from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('https://www.phonepe.com/careers/job-openings/', timeout=30000, wait_until='networkidle')
    page.wait_for_timeout(3000)
    
    # Let's find elements containing 'Full-time' or 'days ago'
    el_list = page.query_selector_all("xpath=//*[contains(text(), 'Full-time')]/..")
    print('Found parent elements count:', len(el_list))
    for i, el in enumerate(el_list[:10]):
        print(f"--- Element {i} ---")
        lines = [l.strip() for l in el.inner_text().split('\n') if l.strip()]
        for j, line in enumerate(lines):
            print(f"  [{j}] {line}")
        # tag name and class name
        c_name = el.evaluate("e => ({tag: e.tagName, cls: e.className, parentCls: e.parentElement ? e.parentElement.className : ''})")
        print("  Info:", c_name)
        # check clickability or link
        a = el.query_selector("a") or el.evaluate_handle("e => e.closest('a')")
        href = a.get_attribute("href") if hasattr(a, 'get_attribute') and a else None
        print("  Href:", href)

    browser.close()
