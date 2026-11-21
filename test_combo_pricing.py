import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

def test_combo_pricing():
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--allow-file-access-from-files")
    opts.add_argument("--window-size=1280,900")
    
    driver = webdriver.Chrome(options=opts)
    file_path = os.path.abspath("docs/index.html")
    url = f"file:///{file_path.replace(os.sep, '/')}"
    
    try:
        driver.get(url)
        time.sleep(1.5)
        
        # Clear cart in localStorage to start completely fresh
        driver.execute_script("localStorage.removeItem('srr_cart'); cart = []; updateCartUI();")
        time.sleep(0.5)
        
        # Verify initial cart count is 0
        assert driver.find_element(By.ID, "cartCountBadge").text == "0"
        print("PASS: Cart is clean (0 items).")
        
        # 1. Test Bridal Duo (₹999)
        driver.execute_script("addComboToCart('bridal');")
        time.sleep(0.5)
        
        subtotal_toast = driver.find_element(By.ID, "toastSubtotal").text
        print(f"Toast subtotal after Bridal Duo: {subtotal_toast}")
        assert subtotal_toast == "₹999", f"Expected ₹999, got {subtotal_toast}"
        
        cart_badge = driver.find_element(By.ID, "cartCountBadge").text
        assert cart_badge == "1", f"Expected count 1, got {cart_badge}"
        print("PASS: Bridal Duo adds at exactly ₹999.")
        
        # Open Cart Drawer to verify item row and subtotal
        driver.execute_script("toggleCartDrawer(true);")
        time.sleep(0.5)
        cart_subtotal = driver.find_element(By.ID, "cartSubtotal").text
        cart_total = driver.find_element(By.ID, "cartTotal").text
        print(f"Cart Drawer subtotal: {cart_subtotal}, total: {cart_total}")
        assert cart_subtotal == "₹999", f"Expected cart subtotal ₹999, got {cart_subtotal}"
        assert cart_total == "₹999", f"Expected cart total ₹999, got {cart_total}"
        print("PASS: Cart drawer verifies subtotal and total are ₹999.")
        
        # Test Proceed to Checkout
        driver.execute_script("proceedToCheckout();")
        time.sleep(0.5)
        checkout_total = driver.find_element(By.ID, "checkoutTotalDisplay").text
        print(f"Checkout Modal total: {checkout_total}")
        assert checkout_total == "₹999", f"Expected checkout total ₹999, got {checkout_total}"
        print("PASS: Checkout modal verifies final payable is ₹999.")
        
        driver.execute_script("closeCheckout();")
        time.sleep(0.5)
        
        # 2. Add Festive Diya & Swan Kit (₹1,899)
        driver.execute_script("addComboToCart('pooja');")
        time.sleep(0.5)
        
        subtotal_toast = driver.find_element(By.ID, "toastSubtotal").text
        expected_two = 999 + 1899
        print(f"Toast subtotal after Diya & Swan: {subtotal_toast} (Expected: ₹{expected_two})")
        assert subtotal_toast == f"₹{expected_two}", f"Expected ₹{expected_two}, got {subtotal_toast}"
        print("PASS: Diya & Swan kit adds at exactly ₹1,899 (Combined: ₹2,898).")
        
        # 3. Add Sankranti Nomu Kit (₹649)
        driver.execute_script("addComboToCart('nomu');")
        time.sleep(0.5)
        
        subtotal_toast = driver.find_element(By.ID, "toastSubtotal").text
        expected_three = 999 + 1899 + 649
        print(f"Toast subtotal after Nomu: {subtotal_toast} (Expected: ₹{expected_three})")
        assert subtotal_toast == f"₹{expected_three}", f"Expected ₹{expected_three}, got {subtotal_toast}"
        print("PASS: Sankranti Nomu kit adds at exactly ₹649 (Combined: ₹3,547).")
        
        # Check Cart Drawer with all 3 combos
        driver.execute_script("toggleCartDrawer(true);")
        time.sleep(0.5)
        
        cart_subtotal = driver.find_element(By.ID, "cartSubtotal").text
        assert cart_subtotal == f"₹{expected_three}"
        
        # Save a screenshot of the cart drawer showing all 3 combos with their prices and savings badges
        drawer_el = driver.find_element(By.ID, "cartDrawer")
        driver.save_screenshot("C:/Users/shash/.gemini/antigravity/brain/5e86c69b-2a03-49d7-ae1b-cbffb0ab610d/cart_combos_pricing_verified.png")
        print("Saved cart_combos_pricing_verified.png")
        
        print("\nALL COMBO PRICING TESTS PASSED 100% PERFECTLY!")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    test_combo_pricing()
