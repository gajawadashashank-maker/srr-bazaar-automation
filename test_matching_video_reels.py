import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

def run():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=412,915")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)
    try:
        file_path = os.path.abspath("docs/index.html")
        driver.get(f"file:///{file_path}")
        time.sleep(2)

        # Test Case 1: 33 Diya Stand (ID: 703481457) -> Must have matching Diya reel
        print("\n[Test 1] 33 Diya Stand (ID: 703481457)")
        driver.execute_script("openQuickView(703481457);")
        time.sleep(1)
        
        vid = driver.find_elements(By.ID, "modalProductVid")
        assert len(vid) == 1, "Diya Stand must have video element!"
        src = vid[0].get_attribute("src")
        print(f" -> Video source: {src}")
        assert "reel_703481457.mp4" in src, f"Expected reel_703481457.mp4, got {src}"
        
        btn_video = driver.find_elements(By.ID, "modalBtnVideo")
        assert len(btn_video) == 1, "Video toggle button must be present!"
        driver.save_screenshot("test_diya_stand_reel.png")
        print(" -> SUCCESS: 33 Diya Stand plays its own dedicated Diya video reel!")

        # Test Case 2: Edu Kondala Nomu (ID: 592133224) -> Must have matching Nomu reel
        print("\n[Test 2] Edu Kondala Nomu (ID: 592133224)")
        driver.execute_script("openQuickView(592133224);")
        time.sleep(1)

        vid = driver.find_elements(By.ID, "modalProductVid")
        assert len(vid) == 1, "Nomu must have video element!"
        src = vid[0].get_attribute("src")
        print(f" -> Video source: {src}")
        assert "reel_592133224.mp4" in src, f"Expected reel_592133224.mp4, got {src}"
        driver.save_screenshot("test_nomu_reel.png")
        print(" -> SUCCESS: Edu Kondala Nomu plays its own dedicated Nomu video reel!")

        # Test Case 3: Swan Tray (ID: 247403588) -> No video reel exists, so NO video button!
        print("\n[Test 3] Swan Tray (ID: 247403588) - Has no video")
        driver.execute_script("openQuickView(247403588);")
        time.sleep(1)

        vid = driver.find_elements(By.ID, "modalProductVid")
        assert len(vid) == 0, "Product without video must NOT render a video element!"
        btn_video = driver.find_elements(By.ID, "modalBtnVideo")
        assert len(btn_video) == 0, "Product without video must NOT render a video toggle button!"
        
        img = driver.find_element(By.ID, "modalProductImg")
        assert img.is_displayed(), "Product photo must be displayed!"
        driver.save_screenshot("test_swan_tray_no_fake_video.png")
        print(" -> SUCCESS: Product without video displays authentic photo and NO mismatched video button!")

        print("\n>>> ALL PRODUCT VIDEO REEL MATCHING TESTS PASSED! <<<")
    finally:
        driver.quit()

if __name__ == "__main__":
    run()
