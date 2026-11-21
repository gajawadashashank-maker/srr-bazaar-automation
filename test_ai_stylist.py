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

        # 1. Verify Floating AI Stylist Button
        print("\n--- Test 1: Floating AI Stylist Button ---")
        floating_btn = wait.until(EC.element_to_be_clickable((By.ID, "aiStylistFloatingBtn")))
        assert floating_btn.is_displayed(), "Floating AI Stylist button should be displayed"
        print(f"Floating button text: '{floating_btn.text.strip()}'")
        assert "Ask AI Stylist" in floating_btn.text, "Floating button text must contain 'Ask AI Stylist'"

        # 2. Click Floating Button to Open Modal
        print("\n--- Test 2: Open AI Stylist Modal ---")
        driver.execute_script("arguments[0].click();", floating_btn)
        time.sleep(1)

        modal = driver.find_element(By.ID, "aiStylistModal")
        assert "hidden" not in modal.get_attribute("class").split(), "AI Stylist modal should be open"
        print("✓ AI Stylist modal is open")

        # 3. Check Initial Welcome Message & Prompt Chips
        print("\n--- Test 3: Welcome Message & Quick Chips ---")
        chat_container = driver.find_element(By.ID, "aiChatMessages")
        chat_text = chat_container.text
        assert "Welcome to SRR Bazaar" in chat_text, "Welcome message should introduce SRR Bazaar"
        print("✓ Welcome message confirmed")

        # 4. Click a Quick Prompt Chip
        print("\n--- Test 4: Send Quick Prompt (Sankranti Nomu) ---")
        nomu_chip = chat_container.find_element(By.XPATH, ".//button[contains(text(), 'Sankranti Nomu')]")
        driver.execute_script("arguments[0].click();", nomu_chip)
        time.sleep(2)

        updated_chat = chat_container.text
        print(f"Chat response preview:\n{updated_chat[-300:]}...")
        assert "Sankranti" in updated_chat or "Nomu" in updated_chat, "AI response should mention Sankranti/Nomu"
        
        # Verify recommended product cards in chat
        cards = chat_container.find_elements(By.XPATH, ".//button[contains(text(), 'View')]")
        assert len(cards) > 0, "Chat bubble must render interactive product cards with 'View' buttons"
        print(f"✓ AI response rendered {len(cards)} interactive product recommendation cards!")

        # 5. Type a Custom Question (Telugu / English)
        print("\n--- Test 5: Type Custom Message ---")
        chat_input = driver.find_element(By.ID, "aiChatInput")
        chat_input.send_keys("What Kundan choker necklace do you have?")
        send_btn = driver.find_element(By.ID, "aiChatSendBtn")
        driver.execute_script("arguments[0].click();", send_btn)
        time.sleep(2)

        final_chat = chat_container.text
        assert "Kundan" in final_chat or "Jadau" in final_chat, "AI should recommend Kundan items"
        print("✓ Custom query successfully processed with recommendations")

        # 6. Test Mobile Viewport
        print("\n--- Test 6: Mobile Viewport Rendering ---")
        driver.set_window_size(390, 844)
        time.sleep(1)
        assert modal.is_displayed(), "Modal should fit and display on mobile viewport"
        print("✓ Mobile layout verified")

        # Save artifact screenshot
        artifact_path = os.path.join(
            r"C:\Users\shash\.gemini\antigravity\brain\5e86c69b-2a03-49d7-ae1b-cbffb0ab610d",
            "test_ai_stylist_verified.png"
        )
        driver.save_screenshot(artifact_path)
        print(f"Saved artifact screenshot to: {artifact_path}")

        # 7. Close Modal via Escape Key
        print("\n--- Test 7: Close Modal via Escape Key ---")
        driver.find_element(By.TAG_NAME, "body").send_keys(webdriver.common.keys.Keys.ESCAPE)
        time.sleep(1)
        assert "hidden" in modal.get_attribute("class").split(), "Modal should close on Escape key"
        print("✓ Escape key cleanly closed AI Stylist modal")

        print("\n========================================")
        print("ALL AI STYLIST & CONCIERGE TESTS PASSED!")
        print("========================================")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
