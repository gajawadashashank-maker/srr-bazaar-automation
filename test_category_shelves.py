import time
from selenium import webdriver
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

opts = EdgeOptions()
opts.add_argument('--headless=new')
opts.add_argument('--window-size=1280,1000')
driver = webdriver.Edge(options=opts)
wait = WebDriverWait(driver, 10)

try:
    url = 'file:///C:/Users/shash/AUTOMATION_WHATSAPP_INSTA/docs/index.html'
    driver.get(url)
    wait.until(EC.presence_of_element_located((By.ID, 'productGrid')))
    time.sleep(1)

    # Initial state
    init_heading = driver.find_element(By.ID, 'catalogueHeading').text
    init_count = driver.find_element(By.ID, 'visibleProductCount').text
    total_count = driver.find_element(By.ID, 'totalProductCount').text
    print(f'Initial state -> Heading: "{init_heading}", Visible: {init_count}, Total: {total_count}')

    # Check 1: Decor category click (Blinkit Circle)
    decor_btn = driver.find_element(By.CSS_SELECTOR, '.category-circle-btn[data-category="decor"]')
    decor_btn.click()
    time.sleep(0.5)
    heading = driver.find_element(By.ID, 'catalogueHeading').text
    count = driver.find_element(By.ID, 'visibleProductCount').text
    print(f'Decor Category Click -> Heading: "{heading}", Count: {count}')
    assert 'Disposables' in heading, f'Heading does not contain Disposables: {heading}'
    assert count == '11', f'Expected 11 items, got {count}'

    # Check 2: Necklaces category click (27 items)
    neck_btn = driver.find_element(By.CSS_SELECTOR, '.category-circle-btn[data-category="necklace"]')
    neck_btn.click()
    time.sleep(0.5)
    heading = driver.find_element(By.ID, 'catalogueHeading').text
    count = driver.find_element(By.ID, 'visibleProductCount').text
    print(f'Necklaces Category Click -> Heading: "{heading}", Count: {count}')
    assert 'Kundan' in heading or 'Choker' in heading, f'Heading mismatch: {heading}'
    assert count == '27', f'Expected 27 items, got {count}'

    # Check 3: All Bazaar category click
    all_btn = driver.find_element(By.CSS_SELECTOR, '.category-circle-btn[data-category="all"]')
    all_btn.click()
    time.sleep(0.5)
    heading = driver.find_element(By.ID, 'catalogueHeading').text
    count = driver.find_element(By.ID, 'visibleProductCount').text
    print(f'All Category Click -> Heading: "{heading}", Count: {count}')
    assert heading == 'Curated Bazaar Aisles'
    assert count == '47'

    # Check 4: Curated Shelves present in All view
    shelf_headings = [h.text for h in driver.find_elements(By.CSS_SELECTOR, '#productGrid h3')]
    print(f'Found {len(shelf_headings)} headings in All view. Shelves & Products preview: {shelf_headings[:6]}')

    print('\n========================================')
    print('ALL CATEGORY CIRCLE & AISLE SHELF CHECKS PASSED!')
    print('========================================')

finally:
    driver.quit()
