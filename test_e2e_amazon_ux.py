import os
import sys
import time
from selenium import webdriver
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def run_e2e_test(target_url="https://srrbazaar.com"):
    print("=" * 60)
    print(f"STARTING E2E FUNCTIONAL TESTING ON {target_url}")
    print("=" * 60)

    options = EdgeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1280,1000")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    results = []

    try:
        driver = webdriver.Edge(options=options)
    except Exception as e:
        print(f"Failed to start Edge WebDriver: {e}")
        return False

    wait = WebDriverWait(driver, 15)

    try:
        # Step 1: Load Page
        print(f"\n[STEP 1] Loading {target_url}...")
        driver.get(target_url)
        wait.until(EC.presence_of_element_located((By.ID, "productGrid")))
        print("✓ Page loaded successfully. Title:", driver.title)
        results.append(("Page Load", "PASS", f"Title: {driver.title}"))

        # Wait for product cards to render
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#productGrid > div")))
        time.sleep(1)

        # Step 2: Grid Add to Cart Interaction
        print("\n[STEP 2] Testing Product Card 'Add to Cart'...")
        card_btn = driver.find_element(By.CSS_SELECTOR, "#productGrid button[title='Add to Cart']")
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", card_btn)
        time.sleep(0.5)
        card_btn.click()
        print("Clicked 'Add to Cart' on product card.")

        time.sleep(0.5)
        # Check if button shows Added
        btn_text = card_btn.text.strip()
        print("Button text immediately after click:", repr(btn_text))
        is_btn_added = "Added" in btn_text

        # Check Amazon Toast
        toast = driver.find_element(By.ID, "amazonCartToast")
        toast_classes = toast.get_attribute("class")
        is_toast_visible = "hidden" not in toast_classes
        toast_subtotal = driver.find_element(By.ID, "toastSubtotal").text.strip()
        print("Toast classes:", toast_classes)
        print("Is Amazon Toast visible?:", is_toast_visible)
        print("Toast Subtotal:", toast_subtotal)

        # Check cart badge
        badge = driver.find_element(By.ID, "cartCountBadge")
        badge_count = badge.text.strip()
        print("Header cart badge count:", badge_count)

        if is_btn_added and is_toast_visible and badge_count in ["1", "2"]:
            results.append(("Card Add to Cart", "PASS", f"Button showed '{btn_text}', Toast visible ({toast_subtotal}), Badge={badge_count}"))
        else:
            results.append(("Card Add to Cart", "FAIL", f"btn={btn_text}, toast_visible={is_toast_visible}, badge={badge_count}"))

        driver.save_screenshot("test_step1_card_added.png")

        # Step 3: Open Product Details (Quick View) Modal
        print("\n[STEP 3] Opening Product Details (Quick View) Modal...")
        product_titles = driver.find_elements(By.CSS_SELECTOR, "#productGrid h3")
        target_card = product_titles[1] if len(product_titles) > 1 else product_titles[0]
        selected_title = target_card.text.strip()
        print(f"Clicking on product: {selected_title}")
        target_card.click()

        wait.until(EC.visibility_of_element_located((By.ID, "quickViewModal")))
        time.sleep(0.5)
        modal = driver.find_element(By.ID, "quickViewModal")
        modal_classes = modal.get_attribute("class")
        print("Quick View Modal opened. Classes:", modal_classes)

        modal_add_btn = driver.find_element(By.ID, "modalAddToCartBtn")
        print("Modal Add to Cart button present. Text:", repr(modal_add_btn.text))

        # Step 4: Click Add to Cart inside Modal (CRITICAL CHECK: MUST NOT CLOSE)
        print("\n[STEP 4] Clicking 'Add to Cart' inside Quick View Modal...")
        modal_add_btn.click()
        time.sleep(0.5)

        # Re-check modal visibility
        modal_still_visible = "hidden" not in modal.get_attribute("class")
        print("Is Quick View Modal STILL open?:", modal_still_visible)

        # Check modal confirmation box
        confirm_box = driver.find_element(By.ID, "modalAddedConfirmation")
        confirm_classes = confirm_box.get_attribute("class")
        is_confirm_visible = "hidden" not in confirm_classes
        print("Amazon confirmation box visible inside modal?:", is_confirm_visible)

        modal_btn_after = driver.find_element(By.ID, "modalAddToCartBtn").text.strip()
        print("Modal button text after click:", repr(modal_btn_after))

        subtotal_text = driver.find_element(By.ID, "modalSubtotalText").text.strip()
        cart_count_text = driver.find_element(By.ID, "modalCartCountText").text.strip()
        print(f"Confirmation subtotal: {subtotal_text}, items: {cart_count_text}")

        driver.save_screenshot("test_step2_modal_added.png")

        if modal_still_visible and is_confirm_visible and "Added to Cart" in modal_btn_after:
            results.append(("Modal Add to Cart UX", "PASS", f"Modal stayed open, Amazon box appeared ({subtotal_text}, {cart_count_text})"))
        else:
            results.append(("Modal Add to Cart UX", "FAIL", f"still_open={modal_still_visible}, box_visible={is_confirm_visible}, btn={modal_btn_after}"))

        # Step 5: Click Proceed to Checkout from Modal Confirmation Box
        print("\n[STEP 5] Clicking 'Proceed to checkout' from modal confirmation box...")
        checkout_btn = confirm_box.find_element(By.XPATH, ".//button[contains(., 'Proceed to checkout')]")
        checkout_btn.click()
        time.sleep(0.5)

        checkout_modal = driver.find_element(By.ID, "checkoutModal")
        is_checkout_visible = "hidden" not in checkout_modal.get_attribute("class")
        modal_now_hidden = "hidden" in modal.get_attribute("class")
        print("Is Checkout Modal visible?:", is_checkout_visible)
        print("Is Quick View Modal now hidden?:", modal_now_hidden)

        checkout_total = driver.find_element(By.ID, "checkoutTotalDisplay").text.strip()
        print("Checkout total display:", checkout_total)

        driver.save_screenshot("test_step3_checkout_modal.png")

        if is_checkout_visible and modal_now_hidden:
            results.append(("Proceed to Checkout Flow", "PASS", f"Checkout opened cleanly, total={checkout_total}"))
        else:
            results.append(("Proceed to Checkout Flow", "FAIL", f"checkout_visible={is_checkout_visible}, qmodal_hidden={modal_now_hidden}"))

        # Close checkout
        close_checkout_btn = checkout_modal.find_element(By.CSS_SELECTOR, "button[onclick='closeCheckout()']")
        close_checkout_btn.click()
        time.sleep(0.5)

        # Step 6: Cart Drawer Verification
        print("\n[STEP 6] Opening Cart Drawer...")
        driver.execute_script("toggleCartDrawer(true);")
        time.sleep(0.5)

        drawer = driver.find_element(By.ID, "cartDrawer")
        is_drawer_visible = "hidden" not in drawer.get_attribute("class")
        drawer_subtotal = driver.find_element(By.ID, "cartSubtotal").text.strip()
        print("Is Cart Drawer visible?:", is_drawer_visible)
        print("Cart Drawer Subtotal:", drawer_subtotal)

        driver.save_screenshot("test_step4_cart_drawer.png")

        if is_drawer_visible:
            results.append(("Cart Drawer", "PASS", f"Drawer opened, subtotal={drawer_subtotal}"))
        else:
            results.append(("Cart Drawer", "FAIL", "Drawer failed to open"))

    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Exception Encountered", "FAIL", str(e)))
    finally:
        driver.quit()

    print("\n" + "=" * 60)
    print("TEST SUMMARY RESULTS")
    print("=" * 60)
    all_passed = True
    for name, status, details in results:
        sym = "✅" if status == "PASS" else "❌"
        print(f"{sym} {name:28}: {status} ({details})")
        if status != "PASS":
            all_passed = False

    return all_passed

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "https://srrbazaar.com"
    success = run_e2e_test(target)
    sys.exit(0 if success else 1)
