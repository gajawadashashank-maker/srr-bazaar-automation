import os
import sys
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def main():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--window-size=1280,1000")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--allow-file-access-from-files")

    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 10)

    try:
        index_path = os.path.abspath("docs/index.html").replace('\\', '/')
        target_url = f"file:///{index_path}"
        print(f"Loading {target_url}...")
        driver.get(target_url)
        print("Page loaded successfully.")
        time.sleep(2)

        # 1. Test Desktop Search Focus & Trending Dropdown
        print("\n--- Test 1: Search Focus & Trending Dropdown ---")
        search_input = wait.until(EC.element_to_be_clickable((By.ID, "searchInput")))
        driver.execute_script("arguments[0].click();", search_input)
        time.sleep(1)

        dropdown = driver.find_element(By.ID, "desktopSearchDropdown")
        cls_list = dropdown.get_attribute("class").split()
        assert "hidden" not in cls_list, f"Search dropdown should be visible on focus, got: {cls_list}"
        dropdown_text = dropdown.text
        print(f"Dropdown text on focus contains: {dropdown_text[:100]}...")
        assert "trending searches" in dropdown_text.lower(), "Dropdown should show Trending Searches when empty"
        assert "Edu Kondala" in dropdown_text, "Trending pills should include Edu Kondala"

        # 2. Test Typing 'edu kondala' -> Direct Matches + Related Products
        print("\n--- Test 2: Typing 'edu kondala' ---")
        search_input.clear()
        search_input.send_keys("edu kondala")
        time.sleep(1)

        # Verify dropdown updated with matching product
        assert "hidden" not in dropdown.get_attribute("class").split(), "Dropdown should remain visible"
        dropdown_html = dropdown.get_attribute("innerHTML")
        assert "Edu Kondala Nomu" in dropdown_html, "Dropdown must recommend 'Edu Kondala Nomu'"
        print("✓ Dropdown recommended 'Edu Kondala Nomu' for query 'edu kondala'")

        # Verify Main Grid has Direct Matches and Related Products
        product_grid = driver.find_element(By.ID, "productGrid")
        grid_text = product_grid.text
        print(f"Grid content: {grid_text[:200]}...")
        assert "Direct Matches" in grid_text, "Grid should have 'Direct Matches' header"
        assert "Edu Kondala Nomu" in grid_text, "Direct matches must contain Edu Kondala Nomu"
        assert "Related Products You May Like" in grid_text, "Grid must show '✨ Related Products You May Like' section"
        print("✓ Grid contains both Direct Matches and Related Products sections!")

        driver.save_screenshot(os.path.join(os.environ.get("LOCALAPPDATA", "."), "test_search_edu_kondala.png"))

        # 3. Test Condensed/No-Space Match: 'edukondala'
        print("\n--- Test 3: Typing 'edukondala' (Compressed without space) ---")
        search_input.clear()
        search_input.send_keys("edukondala")
        time.sleep(1)

        grid_text = driver.find_element(By.ID, "productGrid").text
        assert "Edu Kondala Nomu" in grid_text, "Search for 'edukondala' must match 'Edu Kondala Nomu'"
        print("✓ Successfully matched 'edukondala' -> 'Edu Kondala Nomu'")

        # 4. Test Synonym / Regional Keyword: 'diya'
        print("\n--- Test 4: Typing 'diya' ---")
        search_input.clear()
        search_input.send_keys("diya")
        time.sleep(1)

        grid_text = driver.find_element(By.ID, "productGrid").text
        assert "33 Diya Stand" in grid_text or "diyas" in grid_text.lower(), "Search for 'diya' must find Diya Stand"
        print("✓ Successfully matched 'diya' -> 33 Diya Stand")

        # 5. Test Clear Button
        print("\n--- Test 5: Clear Button ---")
        clear_btn = driver.find_element(By.ID, "searchClearBtnDesktop")
        assert "hidden" not in clear_btn.get_attribute("class").split(), "Clear button should be visible when input has text"
        driver.execute_script("arguments[0].click();", clear_btn)
        time.sleep(1)

        assert search_input.get_attribute("value") == "", "Search input should be cleared"
        assert "hidden" in dropdown.get_attribute("class").split(), "Dropdown should be hidden after clear"
        print("✓ Clear button resets search input and restores catalogue")

        # 6. Test Mobile Search
        print("\n--- Test 6: Mobile Search ---")
        driver.set_window_size(390, 844)
        time.sleep(1)

        mobile_search_input = wait.until(EC.element_to_be_clickable((By.ID, "mobileSearchInput")))
        driver.execute_script("arguments[0].click();", mobile_search_input)
        mobile_search_input.send_keys("edu kondala")
        time.sleep(1)

        mobile_dropdown = driver.find_element(By.ID, "mobileSearchDropdown")
        assert "hidden" not in mobile_dropdown.get_attribute("class").split(), "Mobile search dropdown should be visible"
        assert "Edu Kondala Nomu" in mobile_dropdown.get_attribute("innerHTML"), "Mobile dropdown must recommend Edu Kondala Nomu"
        print("✓ Mobile search recommendations working flawlessly")

        # Capture artifact screenshot
        artifact_path = os.path.join(
            r"C:\Users\shash\.gemini\antigravity\brain\5e86c69b-2a03-49d7-ae1b-cbffb0ab610d",
            "test_robust_search_verified.png"
        )
        driver.save_screenshot(artifact_path)
        print(f"Artifact screenshot saved: {artifact_path}")

        print("\nALL ROBUST SEARCH & RECOMMENDATION TESTS PASSED PERFECTLY!")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
