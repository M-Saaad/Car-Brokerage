import re
import time
import json
import brotli
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from pymongo import MongoClient
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

headers = {
  "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
  "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
  "Accept-Language": "en-US,en;q=0.5",
  "Accept-Encoding": "gzip, deflate, br",
  "Connection": "keep-alive"
}

driver = webdriver.Chrome()

# response = requests.get("https://www.autotempest.com/queue-results?domesticonly=0&localization=any&zip=90210&sort=best_match&sites=te&deduplicationSites=te%7Ccm%7Chem%7Ccs%7Ccv%7Ceb%7Ctc%7Cot%7Cst%7Cfbm&rpp=50&token=5eec92c8ff42297317a3f53f0e00052892b77a627e3fddfcb24bc93d225ead93", headers=headers)

url = 'https://www.autotempest.com/results'

driver.get(url)

def scrape_data():
    data_elements = driver.find_elements(By.XPATH, "//div[@class='result-wrap']")
    for element in data_elements:
        print(element.text)


try:
    sources_btn_xpath = "//button[@id='change-sources-tippy'][1]"
    button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, sources_btn_xpath))
    )
    button.click()

    sources = ['te mash', 'cm mash', 'hem mash', 'cs mash', 'cv mash', 'eb mash', 'tc mash', 'ot mash', 'at ext', 'cg ext', 'st extMash', 'fbm extMash', 'ct ext', 'cgc ext', 'kj ext']

    for source in sources[1:]:
        indicator_div_xpath = f"//span[@class='checkboxWrap  {source}']//div[@class='indicator']"
        indicator_div = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, indicator_div_xpath))
        )
        indicator_div.click()

    sources_update_btn_xpath = "//button[@class='update-results'][1]"
    sources_update_btn = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, sources_update_btn_xpath))
    )
    sources_update_btn.click()

    button_xpath = "//button[@class='more-results'][1]"
    while True:
        try:
            button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, button_xpath))
            )

            driver.execute_script("arguments[0].scrollIntoView(true);", button)
            driver.execute_script("window.scrollBy(0, -200);")

            button.click()
            
            # # Scrape data after the button click
            # scrape_data()
            
            # Optional: Wait for new data to load before the next interaction
            time.sleep(2)
        
        except Exception as e:
            print(f"Button is not available anymore: {e}")
            break  # Exit loop when button is gone (or exception occurs)

finally:
    # Close the WebDriver after scraping is complete
    # driver.quit()
    pass