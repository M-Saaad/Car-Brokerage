import re
import json
import time
from datetime import datetime
from pymongo import MongoClient
from selenium import webdriver
from bson.objectid import ObjectId
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

with open('credential.json') as json_file:
    conn_data = json.load(json_file)
conn_string = conn_data['mongo_conn_string']

client = MongoClient(conn_string)
db = client['test']
reviews_collection = db['reviews']
make_collection = db['makes']
model_collection = db['models']
makess = list(make_collection.find({}, { "name": 1 }))
models = list(model_collection.find({}, { "name": 1 }))

# Set up Chrome options
chrome_options = Options()
# chrome_options.add_argument("--headless")
# chrome_options.add_argument("--no-sandbox")
# chrome_options.add_argument("--disable-dev-shm-usage")

def get_id(col_name, field_value):
    result = None
    global makess
    global models
    global make_collection
    global model_collection
    
    if field_value:
        if col_name == 'makess':
            col_list = makess
        elif col_name == 'models':
            col_list = models

        for doc in col_list:
            if doc.get('name') == field_value:
                result = doc
                break
        
        if result:
            return result.get('_id')
        
        else:
            if col_name == 'makess':
                result = make_collection.insert_one({'name': field_value})
                makess = list(make_collection.find({}, { "name": 1 }))
            elif col_name == 'models':
                result = model_collection.insert_one({'name': field_value})
                models = list(model_collection.find({}, { "name": 1 }))
            return result.inserted_id
    else:
        return None


def get_int(string):
    try:
        return int(re.sub(r'[^\d]', '', string))
    except:
        return None

def recursive_options(xpath, idx):
    options = driver.find_elements(By.XPATH, xpath + "//option")
    try:
        opt = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(options[idx+1])
        )
        opt.click()

        return options[idx+1].text
    except:
        recursive_options(xpath, idx)

if __name__ == "__main__":
    try:

        documents = []

        driver = webdriver.Chrome(options=chrome_options)
        driver.get('https://www.edmunds.com/')

        research_dropdown_xpath = "//button[text()='Research Cars']"
        research_dropdown = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, research_dropdown_xpath))
        )
        research_dropdown.click()

        time.sleep(2)

        make_dropdown_xpath = "//select[@aria-label='Vehicle Make']"
        make_options = driver.find_elements(By.XPATH, make_dropdown_xpath + "//option")
        for make_idx in range(len(make_options[1:5])):
            try:
                make_dropdown = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, make_dropdown_xpath))
                )
                make_dropdown.click()
            except:
                research_dropdown_xpath = "//button[text()='Research Cars']"
                research_dropdown = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, research_dropdown_xpath))
                )
                research_dropdown.click()

                make_dropdown_xpath = "//select[@aria-label='Vehicle Make']"
                make_options = driver.find_elements(By.XPATH, make_dropdown_xpath + "//option")

                #try again
                make_dropdown = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, make_dropdown_xpath))
                )
                make_dropdown.click()

            make = recursive_options(make_dropdown_xpath, make_idx)

            time.sleep(1)

            model_dropdown_xpath = "//select[@aria-label='Vehicle Model']"
            model_options = driver.find_elements(By.XPATH, model_dropdown_xpath + "//option")
            for model_idx in range(len(model_options[1:])):
                try:
                    model_dropdown = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, model_dropdown_xpath))
                    )
                    model_dropdown.click()
                except:
                    research_dropdown_xpath = "//button[text()='Research Cars']"
                    research_dropdown = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, research_dropdown_xpath))
                    )
                    research_dropdown.click()

                    time.sleep(2)

                    #try again
                    make_dropdown = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, make_dropdown_xpath))
                    )
                    make_dropdown.click()

                    time.sleep(1)

                    make_dropdown_xpath = "//select[@aria-label='Vehicle Make']"
                    recursive_options(make_dropdown_xpath, make_idx)

                    time.sleep(1)

                    model_dropdown_xpath = "//select[@aria-label='Vehicle Model']"
                    model_dropdown = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, model_dropdown_xpath))
                    )
                    model_dropdown.click()

                model = recursive_options(model_dropdown_xpath, model_idx)

                time.sleep(1)
                
                year_dropdown_xpath = "//select[@aria-label='Vehicle Year']"
                year_dropdown = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, year_dropdown_xpath))
                )
                year_dropdown.click()
                year_options = driver.find_elements(By.XPATH, year_dropdown_xpath + "//option")
                for year_idx in range(len(year_options[1:])):
                    try:
                        year = year_options[year_idx+1].text
                        year_opt_ = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable(year_options[year_idx+1])
                        )
                        year_opt_.click()
                    except:
                        research_dropdown_xpath = "//button[text()='Research Cars']"
                        research_dropdown = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, research_dropdown_xpath))
                        )
                        research_dropdown.click()

                        time.sleep(2)

                        #try again
                        make_dropdown = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, make_dropdown_xpath))
                        )
                        make_dropdown.click()

                        time.sleep(1)

                        make_dropdown_xpath = "//select[@aria-label='Vehicle Make']"
                        
                        recursive_options(make_dropdown_xpath, make_idx)

                        time.sleep(1)

                        model_options = driver.find_elements(By.XPATH, model_dropdown_xpath + "//option")

                        recursive_options(model_dropdown_xpath, model_idx)

                        year_dropdown = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, year_dropdown_xpath))
                        )
                        year_dropdown.click()

                        recursive_options(year_dropdown_xpath, year_idx)

                    go_button_xpath = "//button[text()='GO']"
                    go_btn = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, go_button_xpath))
                    )
                    go_btn.click()

                    try:
                        title = driver.find_element(By.XPATH, "//h1[@class='css-walxev eyoxkl12']").text
                    except:
                        title = None
                    try:
                        overview = driver.find_element(By.XPATH, "//h2[@title='Overview ']/following-sibling::p").text
                    except:
                        try:
                            overview = driver.find_element(By.XPATH, "//h2[@title='Overview']/following-sibling::p").text
                        except:
                            overview = driver.find_element(By.XPATH, "//h2[@title=' Overview']/following-sibling::p").text
                    try:
                        price = get_int(driver.find_element(By.XPATH, "//span[@class='css-1ha3evc eyoxkl10']").text)
                    except:
                        price = None
                    try:
                        imageUrl = driver.find_element(By.XPATH, "//picture/img").get_attribute('src')
                    except:
                        imageUrl = None

                    try:
                        rating = get_int(driver.find_element(By.XPATH, "//span[@class='css-1e46sgh eky9wq72']").text)
                    except:
                        rating = None

                    description_tags = driver.find_elements(By.XPATH, "//h2[@title='Overview ']/preceding-sibling::h2 | //h2[@title='Overview ']/preceding-sibling::p | //h2[@title='Overview ']/preceding-sibling::ul | //h2[@title='Overview ']/following-sibling::h2 | //h2[@title='Overview ']/following-sibling::p | //h2[@title='Overview ']/following-sibling::ul")[1:]
                    description = []
                    d = {}
                    for tag in description_tags:
                        if tag.tag_name == 'h2':
                            if 'h2' in d.keys():
                                description.append(d)
                                d = {}
                            d['h2'] = tag.text
                        elif tag.tag_name == 'p':
                            d['p'] = tag.text
                        elif tag.tag_name == 'ul':
                            d['ul'] = tag.text.split('\n')

                    if imageUrl:
                        documents.append({
                            'title': title,
                            'description': description,
                            'overview': overview,
                            'make': make,
                            'model': model,
                            'releaseDate': None,
                            'bodyType': None,
                            'transmission': None,
                            'engineSize': None,
                            'engineType': None,
                            'fuelConsumption': None,
                            'price': price,
                            'maxPower': None,
                            'maxTorque': None,
                            'zeroToHundred': None,
                            'imageUrl': imageUrl,
                            'fiveStar': None,
                            'fourStar': None,
                            'threeStar': None,
                            'twoStar': None,
                            'oneStar': None,
                            'analytics': None,
                            'rating': rating,
                            'createdAt': datetime.now(),
                            'updatedAt': datetime.now()
                        })

    finally:
        driver.quit()
