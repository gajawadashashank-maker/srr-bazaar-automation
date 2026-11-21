import os
import sys
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def main():
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--window-size=1280,1000")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--allow-file-access-from-files")

    driver = webdriver.Chrome(options=opts)
    wait = WebDriverWait(driver, 10)

    try:
        index_path = os.path.abspath("docs/index.html").replace('\\', '/')
        target_url = f"file:///{index_path}"
        print(f"Loading {target_url}...")
        driver.get(target_url)
        time.sleep(2)

        # 1. Add product to cart
        print("\n--- Step 1: Add product to cart ---")
        add_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Add to Cart')]")))
        driver.execute_script("arguments[0].click();", add_btn)
        time.sleep(1)

        # 2. Open Cart Drawer
        print("\n--- Step 2: Open Cart Drawer ---")
        cart_btn = driver.find_element(By.XPATH, "//button[contains(@onclick, 'toggleCartDrawer(true)')]")
        driver.execute_script("arguments[0].click();", cart_btn)
        time.sleep(1)

        cart_drawer = driver.find_element(By.ID, "cartDrawer")
        assert "hidden" not in cart_drawer.get_attribute("class").split(), "Cart drawer should be open"
        print("✓ Cart drawer is open")

        # 3. Click Proceed to Checkout
        print("\n--- Step 3: Click Proceed to Order & Pay ---")
        checkout_btn = driver.find_element(By.ID, "checkoutButton")
        driver.execute_script("arguments[0].click();", checkout_btn)
        time.sleep(1)

        checkout_modal = driver.find_element(By.ID, "checkoutModal")
        assert "hidden" not in checkout_modal.get_attribute("class").split(), "Checkout modal should be open"
        assert "hidden" in cart_drawer.get_attribute("class").split(), "Cart drawer should be hidden during checkout"
        print("✓ Checkout modal is open, cart drawer DOM hidden")

        # 4. Test Case 1: Click Top Right 'X' Cross Mark on Checkout Modal
        print("\n--- Test Case 1: Click Top Right 'X' Cross Mark ---")
        close_x_btn = checkout_modal.find_element(By.XPATH, ".//button[@title='Close']")
        driver.execute_script("arguments[0].click();", close_x_btn)
        time.sleep(1)

        assert "hidden" in checkout_modal.get_attribute("class").split(), "Checkout modal should close on X click"
        assert "hidden" not in cart_drawer.get_attribute("class").split(), "Cart drawer MUST reopen when closing checkout!"
        print("✓ SUCCESS: X button returned customer directly to Cart Drawer!")

        # 5. Test Case 2: Click Top Left '←' Back Arrow
        print("\n--- Test Case 2: Click Top Left Back Arrow ---")
        # Proceed again
        driver.execute_script("arguments[0].click();", checkout_btn)
        time.sleep(1)
        assert "hidden" not in checkout_modal.get_attribute("class").split(), "Checkout modal reopened"

        back_arrow_btn = checkout_modal.find_element(By.XPATH, ".//button[contains(@title, 'Back')]")
        driver.execute_script("arguments[0].click();", back_arrow_btn)
        time.sleep(1)

        assert "hidden" in checkout_modal.get_attribute("class").split(), "Checkout modal closed"
        assert "hidden" not in cart_drawer.get_attribute("class").split(), "Cart drawer MUST reopen on Back Arrow click!"
        print("✓ SUCCESS: Top Left Back Arrow returned customer directly to Cart Drawer!")

        # 6. Test Case 3: Click Bottom 'Back to Shopping Cart' Button
        print("\n--- Test Case 3: Click Bottom 'Back to Shopping Cart' Button ---")
        driver.execute_script("arguments[0].click();", checkout_btn)
        time.sleep(1)
        assert "hidden" not in checkout_modal.get_attribute("class").split(), "Checkout modal reopened"

        bottom_back_btn = checkout_modal.find_element(By.XPATH, ".//button[contains(., 'Back to Shopping Cart')]")
        driver.execute_script("arguments[0].click();", bottom_back_btn)
        time.sleep(1)

        assert "hidden" in checkout_modal.get_attribute("class").split(), "Checkout modal closed"
        assert "hidden" not in cart_drawer.get_attribute("class").split(), "Cart drawer MUST reopen on Bottom Back button!"
        print("✓ SUCCESS: Bottom button returned customer directly to Cart Drawer!")

        # 7. Test Case 4: Browser Back / Android Back Gesture (driver.back())
        print("\n--- Test Case 4: Browser / Device Back Gesture (driver.back()) ---")
        driver.execute_script("arguments[0].click();", checkout_btn)
        time.sleep(1)
        assert "hidden" not in checkout_modal.get_attribute("class").split(), "Checkout modal reopened"

        print("Simulating browser / mobile back gesture...")
        driver.back()
        time.sleep(1)

        assert "hidden" in checkout_modal.get_attribute("class").split(), "Checkout modal should close on browser back"
        assert "hidden" not in cart_drawer.get_attribute("class").split(), "Cart drawer MUST reopen on browser back!"
        print("✓ SUCCESS: Browser back gesture returned customer directly to Cart Drawer!")

        # 8. Test Case 5: Close Cart Drawer returns to Home
        print("\n--- Test Case 5: Close Cart Drawer returns to Home ---")
        cart_close_btn = cart_drawer.find_element(By.XPATH, ".//button[contains(@onclick, 'toggleCartDrawer(false)')]")
        driver.execute_script("arguments[0].click();", cart_close_btn)
        time.sleep(1)

        assert "hidden" in cart_drawer.get_attribute("class").split(), "Cart drawer should now close"
        assert "hidden" in checkout_modal.get_attribute("class").split(), "Checkout modal remains closed"
        print("✓ SUCCESS: Cart drawer closed cleanly, user returned to home page!")

        # Save screenshot
        artifact_path = os.path.join(
            r"C:\Users\shash\.gemini\antigravity\brain\5e86c69b-2a03-49d7-ae1b-cbffb0ab610d",
            "test_checkout_back_verified.png"
        )
        driver.save_screenshot(artifact_path)
        print(f"Saved artifact screenshot to: {artifact_path}")

        print("\n========================================")
        print("ALL 5 CHECKOUT BACK NAVIGATION TESTS PASSED!")
        print("========================================")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
