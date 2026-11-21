import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

def test_promo_autoscroll():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=412,915")  # Pixel 7 mobile viewport

    driver = webdriver.Chrome(options=chrome_options)
    try:
        html_path = Path("docs/index.html").resolve()
        driver.get(f"file:///{html_path}")
        time.sleep(1)

        # 1. Verify initially at the top
        initial_scroll = driver.execute_script("return window.pageYOffset;")
        print(f"Initial scroll Y: {initial_scroll}")
        assert initial_scroll == 0, "Initial scroll position should be 0"

        # 2. Find and click the 'Biodegradable Leaf Buffet Plates' promo card
        # Look for the card containing 'Biodegradable Leaf Buffet Plates'
        cards = driver.find_elements(By.XPATH, "//h3[contains(text(), 'Biodegradable Leaf Buffet Plates')]/ancestor::div[contains(@class, 'cursor-pointer')]")
        assert len(cards) > 0, "Biodegradable Leaf Buffet Plates promo card not found"
        promo_card = cards[0]

        print("Clicking 'Biodegradable Leaf Buffet Plates' promo card...")
        driver.execute_script("arguments[0].click();", promo_card)

        # 3. Wait for smooth scroll and filter rendering
        time.sleep(1.5)

        # 4. Check new scroll Y position
        scrolled_y = driver.execute_script("return window.pageYOffset;")
        print(f"Scrolled Y position: {scrolled_y}")
        assert scrolled_y > 200, f"Page did not auto-scroll down! Current Y: {scrolled_y}"

        # 5. Check heading & product grid
        heading = driver.find_element(By.ID, "catalogueHeading").text
        print(f"Catalogue Heading: {heading}")
        assert "Disposables" in heading or "Buffet Plates" in heading, f"Unexpected heading: {heading}"

        # 6. Verify the product card is in view
        products = driver.find_elements(By.XPATH, "//div[@id='productGrid']//h3")
        product_titles = [p.text for p in products]
        print(f"Visible products: {product_titles}")
        assert any("Leaf Buffet Plates" in t for t in product_titles), "Leaf Buffet Plates not visible in filtered grid"

        # Take screenshot for proof
        screenshot_path = Path(r"C:\Users\shash\.gemini\antigravity\brain\5e86c69b-2a03-49d7-ae1b-cbffb0ab610d\test_promo_autoscroll_verified.png")
        driver.save_screenshot(str(screenshot_path))
        print(f"PASS: Screenshot saved to {screenshot_path}")

    finally:
        driver.quit()

if __name__ == "__main__":
    test_promo_autoscroll()
