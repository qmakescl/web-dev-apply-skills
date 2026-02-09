import re
from playwright.sync_api import Page, expect, sync_playwright

def test_home_page(page: Page):
    # Navigate to the home page
    page.goto("http://localhost:8000/")
    
    # Check title
    expect(page).to_have_title(re.compile("Insta-Lite"))
    
    # Check guest section visibility
    guest_section = page.locator("#guest-section")
    expect(guest_section).to_be_visible()
    
    # Check login button in guest section
    login_btn = guest_section.get_by_text("로그인 하러 가기")
    expect(login_btn).to_be_visible()
    
    # Check navigation links
    nav = page.locator("nav")
    expect(nav.get_by_text("로그인")).to_be_visible()
    expect(nav.get_by_text("회원가입")).to_be_visible()

def test_navigation(page: Page):
    page.goto("http://localhost:8000/")
    
    # Click generic login button
    page.get_by_role("link", name="로그인").first.click()
    expect(page).to_have_url(re.compile(".*/login"))
    expect(page.get_by_role("heading", name="로그인")).to_be_visible()
    
    # Go back home
    page.get_by_role("link", name="Insta-Lite").click()
    expect(page).to_have_url(re.compile(".*/$"))
    
    # Click register
    page.get_by_role("link", name="회원가입").first.click()
    expect(page).to_have_url(re.compile(".*/register"))
    expect(page.get_by_role("heading", name="회원가입")).to_be_visible()

if __name__ == "__main__":
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        try:
            print("Running test_home_page...")
            test_home_page(page)
            print("PASS: Home page test")
            
            print("Running test_navigation...")
            test_navigation(page)
            print("PASS: Navigation test")
            
        except Exception as e:
            print(f"FAIL: {e}")
            page.screenshot(path="test_failure.png")
        finally:
            browser.close()
