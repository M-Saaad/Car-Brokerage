import re
import io
import gzip
import time
import json
import brotli
import requests
import pycountry
from datetime import datetime
from bs4 import BeautifulSoup
from pymongo import MongoClient
from selenium import webdriver
from seleniumwire import webdriver
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

client = MongoClient('mongodb+srv://python-team:ERoksQT6kMNyiMSX@cpe.d1cwdad.mongodb.net/?retryWrites=true&w=majority&appName=cpe')
db = client['test']
listing_collection = db['listings']
auctions_collection = db['auctions']
make_collection = db['makes']
model_collection = db['model']
body_type_collection = db['bodytypes']
package_collection = db['packages']
user_id_collection = db['users']
engine_type_collection = db['enginetypes']
color_collection = db['colors']
website_collection = db['websites']
condition_collection = db['conditions']
driver_type_collection = db['drivertypes']
fuel_type_collection = db['fueltypes']
transmission_collection = db['transmissions']

titles = list(listing_collection.find({}, { "title": 1, "_id": 0 }))
titles = [t['title'] for t in titles]

def get_country_name(country_code):
    try:
        # Lookup the country by the ISO alpha-2 code (e.g., 'US' for United States)
        country = pycountry.countries.get(alpha_2=country_code.upper())
        return country.name if country else "Unknown country code"
    except:
        return None
    
def get_int(string):
    try:
        return int(re.sub(r'[^\d]', '', string))
    except:
        return None
    
def upload_data(data):
    data['make'] = get_id(make_collection, {'name': data.get('make')})
    data['model'] = get_id(model_collection, {'name': data.get('model')})
    # data['mileage'] = int(re.sub(r'[^\d]', '', data.get('mileage')))
    data['bodyType'] = get_id(body_type_collection, {'name': data.get('bodyType')})
    data['condition'] = get_id(condition_collection, {'name': data.get('condition')})
    data['transmission'] = get_id(transmission_collection, {'name': data.get('transmission')})
    data['engineType'] = get_id(engine_type_collection, {'name': data.get('engineType')})
    data['color'] = get_id(color_collection, {'name': data.get('color')})
    # data['doors'] = int(re.sub(r'[^\d]', '', data.get('doors')))
    data['website'] = get_id(website_collection, {'name': data.get('website')})
    data['package'] = get_id(package_collection, {'name': data.get('package')})
    data['userId'] = get_id(user_id_collection, {'name': data.get('userId')})

    return data

def get_raw_data():
    listing_documents = []
    auction_documents = []
    
    # Get all network requests
    for i, request in enumerate(driver.requests):
        if request.url.startswith('https://www.autotempest.com/queue-results'):
            if request.response:
                compressed_response = request.response.body
                with gzip.GzipFile(fileobj=io.BytesIO(compressed_response)) as decompressed_file:
                    decompressed_data = decompressed_file.read()
                response_text = json.loads(decompressed_data.decode('utf-8', errors='ignore'))
                # print(
                #     f"URL: {request.url}\n"
                #     f"Method: {request.method}\n"
                #     f"Status code: {request.response.status_code}\n"
                #     f"Response: {response_text}\n"
                # )
                # results.extend(response_text['results'])

                for result in response_text['results']:
                    city = result.get('location').split(',')[0]
                    country = get_country_name(result.get('countryCode'))
                    engine = result.get('trim')
                    title = result.get('title')
                    price = get_int(result.get('price'))
                    description = result.get('details').encode('utf-8').decode('unicode_escape').replace('\n', ' ')
                    mileage = get_int(result.get('mileage'))
                    make = result.get('make')
                    model = result.get('model')
                    year = get_int(result.get('year'))
                    vin = result.get('vin')
                    source = result.get('url').replace('\\', '')
                    website = "AutoTempest"

                    if result.get('img'):
                        image_list = [result.get('img')]
                    else:
                        image_list = None

                    # if source.startswith('https://www.autotempest.com'):
                    #     sub_req = requests.get(source, headers=headers, timeout=15)
                    #     print(i, sub_req.status_code, source)
                    #     if sub_req.status_code == 200:
                    #         sub_soup = BeautifulSoup(sub_req.content, 'html.parser')

                    #         image_list = []
                    #         for img_tag in sub_soup.find_all('img', attrs={'alt': 'Gallery listing photo'})[:-1]:
                    #             image_list.append(img_tag.get('src'))

                    #         for tr in sub_soup.find('div', attrs={'class': 'tab-content'}).find_all('tr'):
                    #             if tr.find_all('td')[0].text == 'Transmission:':
                    #                 transmission = tr.find_all('td')[1].text
                    #             if tr.find_all('td')[0].text == 'Engine:':
                    #                 cylinder = get_int(tr.find_all('td')[1].text)
                    #             if tr.find_all('td')[0].text == 'Interior Color:':
                    #                 color = tr.find_all('td')[1].text
                    #             if tr.find_all('td')[0].text == 'Fuel Type:':
                    #                 fuel_type = tr.find_all('td')[1].text

                        # else:
                    # image_list = None
                    transmission = None
                    cylinder = None
                    color = None
                    fuel_type = None

                    end_date = result.get('endDate')
                    
                    if end_date:
                        bid = int(re.sub(r'[^\d]', '', result.get('currentBid')))
                        auction_documents.append(upload_data({
                            'title': title,
                            'description': description,
                            'make': make,
                            'model': model,
                            'year': year,
                            'mileage': mileage,
                            # 'bodyType': type,
                            'condition': None,
                            'assembly': None, # Not found
                            'vin': vin,
                            'zipCode': None,
                            # 'fuelType': # hamza said not using
                            "driverType": None, # Not found
                            'transmission': transmission,
                            'cylinder': cylinder,
                            'engineSize': engine,
                            'engineType': fuel_type,
                            'registrationStatus': None, # Not found
                            'color': color,
                            'doors': None,
                            'seats': None, # Not found
                            'price': price,
                            'features': None,
                            'imageUrls': image_list,
                            'country': country,
                            'city': city,
                            'website': website,
                            'source': source,
                            'views': 0,
                            'likes': 0,
                            "status": 'Active',
                            "cpePick": False,
                            'soldThrough': None, # Dont know
                            "package": 'Free',
                            "userId": "Admin 1",
                            "createdAt": datetime.now(),
                            "updatedAt": datetime.now(),
                            "bid": bid,
                            "startDate": result.get('ctime'),
                            "endDate": end_date
                        }))
                    else:
                        listing_documents.append(upload_data({
                            'title': title,
                            'description': description,
                            'make': make,
                            'model': model,
                            'year': year,
                            'mileage': mileage,
                            # 'bodyType': type,
                            'condition': None,
                            'assembly': None, # Not found
                            'vin': vin,
                            'zipCode': None,
                            # 'fuelType': # hamza said not using
                            "driverType": None, # Not found
                            'transmission': transmission,
                            'cylinder': cylinder,
                            'engineSize': engine,
                            'engineType': fuel_type,
                            'registrationStatus': None, # Not found
                            'color': color,
                            'doors': None,
                            'seats': None, # Not found
                            'price': price,
                            'features': None,
                            'imageUrls': image_list,
                            'country': country,
                            'city': city,
                            'website': website,
                            'source': source,
                            'views': 0,
                            'likes': 0,
                            "status": 'Active',
                            "cpePick": False,
                            'soldThrough': None, # Dont know
                            "package": 'Free',
                            "userId": "Admin 1",
                            "createdAt": datetime.now(),
                            "updatedAt": datetime.now()
                        }))

    return listing_documents, auction_documents

def get_id(collection, field_value):
    
    if field_value:
        doc = collection.find_one(field_value)

        if doc:
            return doc['_id']
        else:
            result = collection.insert_one(field_value)
            return result.inserted_id
    else:
        return None

# Initialize the WebDriver with Selenium Wire
options = webdriver.ChromeOptions()
driver = webdriver.Chrome(options=options)

# Open the website
driver.get('https://www.autotempest.com/results')  # Replace with the actual URL

sources_btn_xpath = "//button[@id='change-sources-tippy'][1]"
button = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.XPATH, sources_btn_xpath))
)
button.click()

sources = ['cm mash', 'te mash', 'hem mash', 'cs mash', 'cv mash', 'eb mash', 'tc mash', 'ot mash', 'at ext', 'cg ext', 'st extMash', 'fbm extMash', 'ct ext', 'cgc ext', 'kj ext']

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
        time.sleep(3)

    except Exception as e:
        print(f"Button is not available anymore: {e}")
        break  # Exit loop when button is gone (or exception occurs)

listing_documents, auction_documents = get_raw_data()
# listing_documents = upload_data(raw_listing)
# auction_documents = upload_data(raw_auction)
if listing_documents:
    listing_result = listing_collection.insert_many(listing_documents)
    print("Lisitng results:", listing_result)
if auction_documents:
    auction_result = auctions_collection.insert_many(auction_documents)
    print("Auction results:", auction_result)
