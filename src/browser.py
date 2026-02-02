
from playwright.sync_api import sync_playwright

def goto_and_select(full_url, selector, page=None):
    if page is not None:
        page.goto(full_url)
        page.wait_for_selector(selector, timeout=10000)
        return page.inner_html(selector)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(full_url)
        page.wait_for_selector(selector, timeout=10000)
        return page.inner_html(selector)