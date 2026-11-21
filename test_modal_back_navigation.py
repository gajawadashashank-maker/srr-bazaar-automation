import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def run_test():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=412,915") # Mobile viewport
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)
    try:
        # Load local docs/index.html via absolute file path
        file_path = os.path.abspath("docs/index.html")
        driver.get(f"file:///{file_path}")
        time.sleep(2)

        print("[Test 1] Verify initial page load")
        assert "SRR Bazaar" in driver.title
        initial_url = driver.current_url
        print(f" -> Initial URL: {initial_url}")

        # Step 1: Add item to cart
        print("\n[Test 2] Add item to cart & Open Cart Drawer")
        add_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Add to Cart')]")
        driver.execute_script("arguments[0].click();", add_btn)
        time.sleep(1)

        # Open cart drawer
        cart_btn = driver.find_element(By.XPATH, "//button[contains(@onclick, 'toggleCartDrawer(true)')]")
        driver.execute_script("arguments[0].click();", cart_btn)
        time.sleep(0.8)

        cart_drawer = driver.find_element(By.ID, "cartDrawer")
        assert "hidden" not in cart_drawer.get_attribute("class"), "Cart drawer should be open!"
        print(" -> Cart drawer is successfully OPEN.")

        # Simulate mobile browser back button (driver.back())
        print("\n[Test 3] User presses Back Button instead of 'X' button")
        driver.back()
        time.sleep(0.8)

        cart_drawer = driver.find_element(By.ID, "cartDrawer")
        assert "hidden" in cart_drawer.get_attribute("class"), "Cart drawer should be HIDDEN after pressing back!"
        assert driver.current_url == initial_url, "User should still be on SRR Bazaar storefront, NOT exited!"
        print(" -> SUCCESS: Cart drawer CLOSED cleanly on Back Button. Storefront did NOT exit!")

        # Step 2: Open Quick View Modal & Back Button
        print("\n[Test 4] Open Product Detail / Quick View Modal & press Back Button")
        driver.execute_script("openQuickView(286241428);")
        time.sleep(1)

        quick_modal = driver.find_element(By.ID, "quickViewModal")
        assert "hidden" not in quick_modal.get_attribute("class"), "Quick view modal should be OPEN!"
        print(" -> Quick view modal is OPEN.")

        driver.back()
        time.sleep(0.8)

        quick_modal = driver.find_element(By.ID, "quickViewModal")
        assert "hidden" in quick_modal.get_attribute("class"), "Quick view modal should be HIDDEN after back button!"
        assert driver.current_url == initial_url, "User should still be on SRR Bazaar storefront!"
        print(" -> SUCCESS: Quick View modal CLOSED cleanly on Back Button.")

        # Step 3: Open Tracking Modal & Back Button
        print("\n[Test 5] Open Live Tracking Modal & press Back Button")
        driver.execute_script("openTrackingModal();")
        time.sleep(0.8)

        track_modal = driver.find_element(By.ID, "trackingModal")
        assert "hidden" not in track_modal.get_attribute("class"), "Tracking modal should be OPEN!"
        print(" -> Tracking modal is OPEN.")

        driver.back()
        time.sleep(0.8)

        track_modal = driver.find_element(By.ID, "trackingModal")
        assert "hidden" in track_modal.get_attribute("class"), "Tracking modal should be HIDDEN after back button!"
        print(" -> SUCCESS: Tracking modal CLOSED cleanly on Back Button.")

        # Step 4: Checkout Modal & Back Button
        print("\n[Test 6] Open Checkout Modal & press Back Button")
        driver.execute_script("proceedToCheckout();")
        time.sleep(0.8)

        checkout_modal = driver.find_element(By.ID, "checkoutModal")
        assert "hidden" not in checkout_modal.get_attribute("class"), "Checkout modal should be OPEN!"
        print(" -> Checkout modal is OPEN.")

        driver.back()
        time.sleep(0.8)

        checkout_modal = driver.find_element(By.ID, "checkoutModal")
        assert "hidden" in checkout_modal.get_attribute("class"), "Checkout modal should be HIDDEN after back button!"
        print(" -> SUCCESS: Checkout modal CLOSED cleanly on Back Button.")

        # Step 5: Keyboard Escape key test
        print("\n[Test 7] Open Cart Drawer & press Escape key")
        driver.execute_script("toggleCartDrawer(true);")
        time.sleep(0.5)
        assert "hidden" not in driver.find_element(By.ID, "cartDrawer").get_attribute("class")

        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        time.sleep(0.8)
        assert "hidden" in driver.find_element(By.ID, "cartDrawer").get_attribute("class")
        print(" -> SUCCESS: Escape key cleanly closes open drawer/modal.")

        # Capture verification screenshot
        driver.save_screenshot("test_modal_back_verified.png")
        print("\n>>> ALL BACK BUTTON & HISTORY NAVIGATION TESTS PASSED! <<<")

    finally:
        driver.quit()

if __name__ == "__main__":
    run_test()
