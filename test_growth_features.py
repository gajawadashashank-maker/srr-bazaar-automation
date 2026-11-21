import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def run_test():
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--allow-file-access-from-files")
    opts.add_argument("--window-size=1280,900")
    
    driver = webdriver.Chrome(options=opts)
    
    file_path = os.path.abspath("docs/index.html")
    url = f"file:///{file_path.replace(os.sep, '/')}"
    print(f"Loading URL: {url}")
    
    try:
        driver.get(url)
        time.sleep(2)
        
        # 1. Check Console Logs for JS Errors
        logs = driver.get_log('browser')
        errors = [log for log in logs if log['level'] == 'SEVERE']
        if errors:
            print("WARNING: Severe browser console errors detected:")
            for err in errors:
                print("  ", err['message'])
        else:
            print("PASS: Zero severe browser console errors.")

        # 2. Test Frequently Bought Together (Combo Bundles)
        combo_section = driver.find_element(By.ID, "comboBundlesSection")
        assert combo_section.is_displayed(), "Combo section not visible"
        print("PASS: Frequently Bought Together section is displayed.")
        
        # Click Add 2-Piece Bridal Duo to Cart
        bridal_btn = combo_section.find_elements(By.TAG_NAME, "button")[0]
        driver.execute_script("arguments[0].click();", bridal_btn)
        time.sleep(1)
        
        # Verify Cart Count is at least 1 (unified combo item)
        cart_badge = driver.find_element(By.ID, "cartCountBadge")
        print(f"Cart count after adding combo: {cart_badge.text}")
        assert int(cart_badge.text) >= 1, f"Expected cart count >= 1, got {cart_badge.text}"
        print("PASS: Bridal Combo successfully added to cart.")
        
        # 3. Test Live Order Tracking Modal
        track_btn = driver.find_element(By.XPATH, "//button[contains(., 'Track')]")
        driver.execute_script("arguments[0].click();", track_btn)
        time.sleep(1)
        
        tracking_modal = driver.find_element(By.ID, "trackingModal")
        assert not "hidden" in tracking_modal.get_attribute("class"), "Tracking modal did not open"
        print("PASS: Tracking modal opened successfully.")
        
        # Test simulated lookup
        track_input = driver.find_element(By.ID, "trackInputQuery")
        track_input.clear()
        track_input.send_keys("9948633303")
        
        lookup_btn = tracking_modal.find_element(By.XPATH, ".//button[contains(@onclick, 'executeTrackLookup')]")
        lookup_btn.click()
        time.sleep(1)
        
        result_area = driver.find_element(By.ID, "trackingResultArea")
        assert "The Professional Couriers" in result_area.text, "Professional Couriers not in tracking result"
        assert "Armoor" in result_area.text, "Armoor not in tracking result"
        print("PASS: Order tracking lookup verified with The Professional Couriers (Armoor Hub).")
        
        # Close tracking modal
        close_btn = tracking_modal.find_element(By.XPATH, ".//button[contains(@onclick, 'closeTrackingModal')]")
        close_btn.click()
        time.sleep(0.5)
        
        # 4. Test Customer Reviews & WhatsApp Unboxings Proof Section
        reviews_section = driver.find_element(By.ID, "reviewsProofSection")
        assert reviews_section.is_displayed(), "Reviews proof section not displayed"
        assert "Sravanthi Rao" in reviews_section.text
        assert "Kavitha Mudiraj" in reviews_section.text
        assert "The Professional Couriers" in reviews_section.text
        print("PASS: Customer Reviews & WhatsApp Unboxing Proof section is verified.")
        
        # 5. Test Product Card Video Reel Badge & Quick View Reel Toggle
        qv_triggers = driver.find_elements(By.XPATH, "//div[contains(@onclick, 'openQuickView')]")
        print(f"Found {len(qv_triggers)} quick view triggers on screen.")
        assert len(qv_triggers) > 0, "No quick view triggers found"
        
        # Click first product to open quick view
        driver.execute_script("arguments[0].click();", qv_triggers[0])
        time.sleep(1)
        
        quick_modal = driver.find_element(By.ID, "quickViewModal")
        assert not "hidden" in quick_modal.get_attribute("class"), "Quick view modal not open"
        print("PASS: Quick view modal opened.")
        
        # Switch to Video Reel
        video_btn = driver.find_element(By.ID, "modalBtnVideo")
        video_btn.click()
        time.sleep(1)
        
        vid_element = driver.find_element(By.ID, "modalProductVid")
        assert not "hidden" in vid_element.get_attribute("class"), "Video element is hidden"
        print("PASS: Video reel successfully activated and visible in modal.")
        
        # Save screenshot of video modal
        driver.save_screenshot("test_growth_video_modal.png")
        print("Screenshot saved to test_growth_video_modal.png")
        
        # Close quick view
        close_qv = quick_modal.find_element(By.XPATH, ".//button[contains(@onclick, 'closeQuickView')]")
        close_qv.click()
        time.sleep(0.5)
        
        # Save screenshot of combo & reviews on mobile viewport
        driver.set_window_size(390, 844)
        time.sleep(1)
        driver.save_screenshot("test_growth_mobile_view.png")
        print("Mobile screenshot saved to test_growth_mobile_view.png")
        
        print("\nALL 4 STRATEGIC GROWTH FEATURES VERIFIED AND PASSING!")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    run_test()
