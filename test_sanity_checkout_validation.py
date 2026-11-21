import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

def test_sanity_checkout_validation():
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--window-size=1280,900")

    driver = webdriver.Chrome(options=opts)
    file_path = os.path.abspath("docs/index.html")
    url = f"file:///{file_path.replace(os.sep, '/')}"

    try:
        driver.get(url)
        time.sleep(1.5)

        # 1. Test Body Scroll Lock when Cart Drawer opens
        body_class = driver.find_element(By.TAG_NAME, "body").get_attribute("class")
        assert "overflow-hidden" not in body_class, "Body should not have overflow-hidden initially"

        driver.execute_script("toggleCartDrawer(true);")
        time.sleep(0.5)
        body_class = driver.find_element(By.TAG_NAME, "body").get_attribute("class")
        assert "overflow-hidden" in body_class, "Body must have overflow-hidden when cart drawer is open"
        print("PASS: Scroll lock active when drawer opens.")

        driver.execute_script("toggleCartDrawer(false);")
        time.sleep(0.5)
        body_class = driver.find_element(By.TAG_NAME, "body").get_attribute("class")
        assert "overflow-hidden" not in body_class, "Body must restore scroll when drawer closes"
        print("PASS: Scroll lock released when drawer closes.")

        # 2. Add an item to cart and open checkout
        driver.execute_script("addToCart(703481457); proceedToCheckout();")
        time.sleep(0.5)

        checkout_modal = driver.find_element(By.ID, "checkoutModal")
        assert not "hidden" in checkout_modal.get_attribute("class"), "Checkout modal should be open"
        print("PASS: Checkout modal opened with product 703481457.")

        # 3. Test Invalid Mobile Number Validation (< 10 digits)
        driver.execute_script("""
            document.getElementById('custName').value = 'Ramesh Rao';
            document.getElementById('custPhone').value = '98765'; // invalid 5 digits
            document.getElementById('custAddress').value = 'House 12, Main Street';
            document.getElementById('custPincode').value = '503224';
            document.getElementById('custCity').value = 'Armoor';
            document.getElementById('custState').value = 'Telangana';
            handlePaymentMethodChange('cod');
        """)
        time.sleep(0.5)

        # Attempt submit and catch alert
        driver.execute_script("submitFinalOrder();")
        time.sleep(0.5)

        alert = driver.switch_to.alert
        alert_text = alert.text
        print(f"Validation Alert text: {alert_text}")
        assert "10-digit mobile number" in alert_text, f"Expected mobile validation alert, got: {alert_text}"
        alert.accept()
        print("PASS: Invalid phone number (<10 digits) correctly blocked.")

        # 4. Test Invalid Pincode Validation (< 6 digits)
        driver.execute_script("""
            document.getElementById('custPhone').value = '9876543210';
            document.getElementById('custPincode').value = '503'; // invalid 3 digits
        """)
        time.sleep(0.5)
        driver.execute_script("submitFinalOrder();")
        time.sleep(0.5)

        alert = driver.switch_to.alert
        alert_text = alert.text
        print(f"Pincode Alert text: {alert_text}")
        assert "6-digit postal pincode" in alert_text, f"Expected pincode validation alert, got: {alert_text}"
        alert.accept()
        print("PASS: Invalid pincode (<6 digits) correctly blocked.")

        # 5. Test Successful Order Submission
        driver.execute_script("""
            document.getElementById('custPincode').value = '503224';
        """)
        time.sleep(0.5)
        driver.execute_script("submitFinalOrder();")
        time.sleep(1)

        success_modal = driver.find_element(By.ID, "orderSuccessModal")
        assert not "hidden" in success_modal.get_attribute("class"), "Order success modal should be visible"

        order_id = driver.find_element(By.ID, "successOrderId").text
        print(f"Order created successfully with ID: {order_id}")
        assert order_id.startswith("SRR-"), f"Unexpected Order ID: {order_id}"

        wa_btn = driver.find_element(By.ID, "successWhatsAppBtn")
        wa_href = wa_btn.get_attribute("href")
        assert "@sujatha60861" in wa_href or "sujatha60861" in wa_href, "WhatsApp link should reference store handle"
        print("PASS: Complete order submission, order ID generation, and WhatsApp redirect verified.")

    finally:
        driver.quit()

if __name__ == "__main__":
    test_sanity_checkout_validation()
