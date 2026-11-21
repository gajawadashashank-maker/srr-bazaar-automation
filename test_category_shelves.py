import os
import sys
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

target_url = sys.argv[1] if len(sys.argv) > 1 else 'file:///C:/Users/shash/AUTOMATION_WHATSAPP_INSTA/docs/index.html'

opts = Options()
opts.add_argument('--headless=new')
opts.add_argument('--window-size=1280,1000')
driver = webdriver.Chrome(options=opts)
wait = WebDriverWait(driver, 15)

try:
    print(f"Testing categories & shelves on {target_url}...")
    driver.get(target_url)
    wait.until(EC.presence_of_element_located((By.ID, 'productGrid')))
    time.sleep(1)

    # Initial state
    init_heading = driver.find_element(By.ID, 'catalogueHeading').text
    init_count = driver.find_element(By.ID, 'visibleProductCount').text
    total_count = driver.find_element(By.ID, 'totalProductCount').text
    print(f'Initial state -> Heading: "{init_heading}", Visible: {init_count}, Total: {total_count}')
    assert total_count == '47', f'Expected 47 total items, got {total_count}'

    # Check 1: Decor category click (Pooja & Festive Decor)
    decor_btn = driver.find_element(By.CSS_SELECTOR, '.category-circle-btn[data-category="decor"]')
    driver.execute_script("arguments[0].click();", decor_btn)
    time.sleep(0.5)
    heading = driver.find_element(By.ID, 'catalogueHeading').text
    count = driver.find_element(By.ID, 'visibleProductCount').text
    print(f'Decor Category Click -> Heading: "{heading}", Count: {count}')
    assert 'Decor' in heading or 'Pooja' in heading, f'Heading does not contain Decor/Pooja: {heading}'
    assert count == '12', f'Expected 12 items, got {count}'

    # Check 2: Buffet Plates category click (1 item)
    buffet_btn = driver.find_element(By.CSS_SELECTOR, '.category-circle-btn[data-category="disposables"]')
    driver.execute_script("arguments[0].click();", buffet_btn)
    time.sleep(0.5)
    heading = driver.find_element(By.ID, 'catalogueHeading').text
    count = driver.find_element(By.ID, 'visibleProductCount').text
    print(f'Buffet Plates Category Click -> Heading: "{heading}", Count: {count}')
    assert 'Buffet' in heading or 'Eco' in heading, f'Heading mismatch: {heading}'
    assert count == '1', f'Expected 1 item, got {count}'

    # Check 3: Necklaces category click (23 items)
    neck_btn = driver.find_element(By.CSS_SELECTOR, '.category-circle-btn[data-category="necklace"]')
    driver.execute_script("arguments[0].click();", neck_btn)
    time.sleep(0.5)
    heading = driver.find_element(By.ID, 'catalogueHeading').text
    count = driver.find_element(By.ID, 'visibleProductCount').text
    print(f'Necklaces Category Click -> Heading: "{heading}", Count: {count}')
    assert 'Kundan' in heading or 'Choker' in heading, f'Heading mismatch: {heading}'
    assert count == '23', f'Expected 23 items, got {count}'

    # Check 4: All Bazaar category click
    all_btn = driver.find_element(By.CSS_SELECTOR, '.category-circle-btn[data-category="all"]')
    driver.execute_script("arguments[0].click();", all_btn)
    time.sleep(0.5)
    heading = driver.find_element(By.ID, 'catalogueHeading').text
    count = driver.find_element(By.ID, 'visibleProductCount').text
    print(f'All Category Click -> Heading: "{heading}", Count: {count}')
    assert heading == 'Curated Bazaar Aisles'
    assert count == '47'

    # Check 5: Curated Shelves present in All view
    shelf_headings = [h.text for h in driver.find_elements(By.CSS_SELECTOR, '#productGrid h3')]
    print(f'Found {len(shelf_headings)} headings in All view. Shelves preview: {shelf_headings[:6]}')

    print('\n========================================')
    print('ALL CATEGORY CIRCLE & AISLE SHELF CHECKS PASSED!')
    print('========================================')

finally:
    driver.quit()
