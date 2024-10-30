import re
import io
import gzip
import time
import json
import pycountry
from datetime import datetime
from pymongo import MongoClient
from selenium import webdriver
from seleniumwire import webdriver
from bson.objectid import ObjectId
from selenium.webdriver.chrome.options import Options
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

with open('credential.json') as json_file:
    conn_data = json.load(json_file)
conn_string = conn_data['mongo_conn_string']

client = MongoClient(conn_string)
db = client['test']
listing_collection = db['listings']
auctions_collection = db['auctions']
make_collection = db['makes']
model_collection = db['models']
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
makess = list(make_collection.find({}, { "name": 1 }))
models = list(model_collection.find({}, { "name": 1 }))
body_types = list(body_type_collection.find({}, { "name": 1 }))
packages = list(package_collection.find({}, { "name": 1 }))
user_ids = list(user_id_collection.find({}, { "name": 1 }))
engine_types = list(engine_type_collection.find({}, { "name": 1 }))
colors = list(color_collection.find({}, { "name": 1 }))
websites = list(website_collection.find({}, { "name": 1 }))
conditions = list(condition_collection.find({}, { "name": 1 }))
driver_types = list(driver_type_collection.find({}, { "name": 1 }))
fuel_types = list(fuel_type_collection.find({}, { "name": 1 }))
transmissions = list(transmission_collection.find({}, { "name": 1 }))

listing_docs = list(listing_collection.find({"webiste": ObjectId('670d3996b3c83649dab17ec4')}, { "title": 1, "mileage": 1, "_id": 0 }))
titles = [t['title'] for t in listing_docs]
mileages = [m['mileage'] for m in listing_docs]
auction_docs = list(auctions_collection.find({"webiste": ObjectId('670d3996b3c83649dab17ec4')}, { "title": 1, "mileage": 1, "_id": 0 }))
titles.extend([t['title'] for t in auction_docs])
mileages.extend([m.get('mileage') for m in auction_docs])

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
    data['make'] = get_id('makess', data.get('make'))
    data['model'] = get_id('models', data.get('model'))
    # data['mileage'] = int(re.sub(r'[^\d]', '', data.get('mileage')))
    data['bodyType'] = get_id('body_types', data.get('bodyType'))
    data['condition'] = get_id('conditions', data.get('condition'))
    data['transmission'] = get_id('transmissions', data.get('transmission'))
    data['engineType'] = get_id('engine_types', data.get('engineType'))
    data['color'] = get_id('colors', data.get('color'))
    # data['doors'] = int(re.sub(r'[^\d]', '', data.get('doors')))
    data['website'] = get_id('websites', data.get('website'))
    data['package'] = get_id('packages', data.get('package'))
    data['userId'] = get_id('user_ids', data.get('userId'))

    return data

def get_raw_data(break_flag):
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
                    website = "Car"

                    if title in titles and mileage in mileages:
                        print("Skipping!!!")
                        break_flag = True
                        break

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
        if break_flag:
            break

    return break_flag, listing_documents, auction_documents

def get_id(col_name, field_value):
    result = None
    global makess
    global models
    global body_types
    global packages
    global user_ids
    global engine_types
    global colors
    global websites
    global conditions
    global driver_types
    global fuel_types
    global transmissions
    global make_collection
    global model_collection
    global body_type_collection
    global package_collection
    global user_id_collection
    global engine_type_collection
    global color_collection
    global website_collection
    global condition_collection
    global driver_type_collection
    global fuel_type_collection
    global transmission_collection
    
    if field_value:
        if col_name == 'makess':
            col_list = makess
        elif col_name == 'models':
            col_list = models
        elif col_name == 'body_types':
            col_list = body_types
        elif col_name == 'packages':
            col_list = packages
        elif col_name == 'user_ids':
            col_list = user_ids
        elif col_name == 'engine_types':
            col_list = engine_types
        elif col_name == 'colors':
            col_list = colors
        elif col_name == 'websites':
            col_list = websites
        elif col_name == 'conditions':
            col_list = conditions
        elif col_name == 'driver_types':
            col_list = driver_types
        elif col_name == 'fuel_types':
            col_list = fuel_types
        elif col_name == 'transmissions':
            col_list = transmissions

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
            elif col_name == 'body_types':
                result = body_type_collection.insert_one({'name': field_value})
                body_types = list(body_type_collection.find({}, { "name": 1 }))
            elif col_name == 'packages':
                result = package_collection.insert_one({'name': field_value})
                packages = list(package_collection.find({}, { "name": 1 }))
            elif col_name == 'user_ids':
                result = user_id_collection.insert_one({'name': field_value})
                user_ids = list(user_id_collection.find({}, { "name": 1 }))
            elif col_name == 'engine_types':
                result = engine_type_collection.insert_one({'name': field_value})
                engine_types = list(engine_type_collection.find({}, { "name": 1 }))
            elif col_name == 'colors':
                result = model_collection.insert_one({'name': field_value})
                colors = list(color_collection.find({}, { "name": 1 }))
            elif col_name == 'websites':
                result = website_collection.insert_one({'name': field_value})
                websites = list(website_collection.find({}, { "name": 1 }))
            elif col_name == 'conditions':
                result = condition_collection.insert_one({'name': field_value})
                conditions = list(condition_collection.find({}, { "name": 1 }))
            elif col_name == 'driver_types':
                result = driver_type_collection.insert_one({'name': field_value})
                driver_types = list(driver_type_collection.find({}, { "name": 1 }))
            elif col_name == 'fuel_types':
                result = fuel_type_collection.insert_one({'name': field_value})
                fuel_types = list(fuel_type_collection.find({}, { "name": 1 }))
            elif col_name == 'transmissions':
                result = transmission_collection.insert_one({'name': field_value})
                transmissions = list(transmission_collection.find({}, { "name": 1 }))
            return result.inserted_id
    else:
        return None

# Initialize the WebDriver with Selenium Wire
# Set up Chrome options
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run Chrome in headless mode
chrome_options.add_argument("--no-sandbox")  # Bypass OS security model, needed for some servers
chrome_options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems
chrome_options.add_argument("--remote-debugging-port=9222")  # Needed to fix DevToolsActivePort file issue

# Set up the driver with the options
driver = webdriver.Chrome(options=chrome_options)

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

sort_dropdown = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.XPATH, "//select[@id='sort']"))
)
sort_dropdown.click()
newest_option = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.XPATH, "//select[@id='sort']//option[@value='date_desc']"))
)
newest_option.click()

listing_documents = []
auction_documents = []
break_flag = False

del driver.requests
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

        break_flag, temp_listing, temp_auction = get_raw_data(break_flag)
        listing_documents.extend(temp_listing)
        auction_documents.extend(temp_auction)
        del driver.requests

        if break_flag:
            break

    except Exception as e:
        print(f"Button is not available anymore: {e}")
        break  # Exit loop when button is gone (or exception occurs)

# listing_documents = upload_data(raw_listing)
# auction_documents = upload_data(raw_auction)
if listing_documents:
    listing_result = listing_collection.insert_many(listing_documents)
    print("length: ", len(listing_documents))
if auction_documents:
    auction_result = auctions_collection.insert_many(auction_documents)
    print("length: ", len(auction_documents))
