import os
import sys
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def test_viewport(device_spec):
    if isinstance(device_spec, str):
        device_name = device_spec
        emulation = {"deviceName": device_name}
    else:
        device_name = device_spec["name"]
        emulation = {"deviceMetrics": {"width": device_spec["width"], "height": device_spec["height"], "pixelRatio": 3.0}}

    print(f"\n==========================================")
    print(f"Testing Device: {device_name}")
    print(f"==========================================")
    opts = Options()
    opts.add_argument('--headless=new')
    opts.add_experimental_option("mobileEmulation", emulation)
    opts.add_argument('--no-sandbox')
    opts.add_argument('--allow-file-access-from-files')

    driver = webdriver.Chrome(options=opts)
    try:
        index_path = os.path.abspath('docs/index.html').replace('\\', '/')
        driver.get(f'file:///{index_path}')
        time.sleep(2)

        # 1. Verify Document Width Metrics
        metrics = driver.execute_script("""
            return {
                winWidth: window.innerWidth,
                docClient: document.documentElement.clientWidth,
                docScroll: document.documentElement.scrollWidth,
                bodyClient: document.body.clientWidth,
                bodyScroll: document.body.scrollWidth
            };
        """)
        print(f"Viewport innerWidth: {metrics['winWidth']}px")
        print(f"Document clientWidth: {metrics['docClient']}px | scrollWidth: {metrics['docScroll']}px")
        print(f"Body clientWidth: {metrics['bodyClient']}px | scrollWidth: {metrics['bodyScroll']}px")

        # Crucial assertion: Document must NOT have horizontal scroll!
        assert metrics['docScroll'] <= metrics['docClient'] + 1, (
            f"Horizontal document overflow detected on {device_name}! "
            f"scrollWidth ({metrics['docScroll']}px) > clientWidth ({metrics['docClient']}px)"
        )
        print("✓ Zero document-level horizontal overflow confirmed!")

        # 2. Simulate Horizontal Swipe / Scroll Attempts
        scroll_attempt = driver.execute_script("""
            window.scrollTo(500, 0);
            const x1 = window.scrollX;
            window.scrollBy(300, 0);
            const x2 = window.scrollX;
            return { x1, x2 };
        """)
        print(f"ScrollX after scrollTo(500,0): {scroll_attempt['x1']}px")
        assert scroll_attempt['x1'] == 0, "Page should not scroll horizontally!"
        assert scroll_attempt['x2'] == 0, "Page should not scroll horizontally!"
        print("✓ Horizontal swiping is strictly locked. No empty space can be revealed on the right!")

        # 3. Check Header Action Buttons Fit Inside Screen
        header_check = driver.execute_script("""
            const badge = document.getElementById('cartCountBadge');
            const cartBtn = badge ? badge.closest('button') : null;
            const docWidth = document.documentElement.clientWidth;
            if (cartBtn) {
                const rect = cartBtn.getBoundingClientRect();
                return {
                    cartBtnRight: rect.right,
                    docWidth: docWidth,
                    fits: rect.right <= docWidth
                };
            }
            return { fits: true };
        """)
        print(f"Cart button check: {header_check}")
        assert header_check['fits'], "Cart button must fit within screen bounds!"
        print("✓ Header buttons cleanly contained within mobile screen width!")

        # 4. Save Screenshot Artifact
        artifact_path = os.path.join(
            r"C:\Users\shash\.gemini\antigravity\brain\5e86c69b-2a03-49d7-ae1b-cbffb0ab610d",
            f"test_mobile_no_overflow_{device_name.replace(' ', '_').lower()}.png"
        )
        driver.save_screenshot(artifact_path)
        print(f"Saved artifact screenshot to: {artifact_path}")

    finally:
        driver.quit()

def main():
    # Test on multiple popular mobile viewports
    test_viewport("Pixel 7")                                            # 412px
    test_viewport("iPhone SE")                                           # 375px
    test_viewport({"name": "Android Compact (360px)", "width": 360, "height": 740}) # 360px
    print("\n==========================================")
    print("ALL MOBILE OVERFLOW & SWIPE TESTS PASSED!")
    print("==========================================")

if __name__ == "__main__":
    main()
