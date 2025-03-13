import re
import os
import sys
import time
import json
import requests
import numpy as np
from PIL import Image
from io import BytesIO
import tensorflow as tf
from bs4 import BeautifulSoup
from datetime import datetime
from pymongo import MongoClient
from bson.objectid import ObjectId
# from tensorflow.keras.preprocessing import image
# from sklearn.metrics.pairwise import cosine_similarity
# from tensorflow.keras.applications import EfficientNetB0

headers = {
  "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36",
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
collection = db['listings']
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

listing_docs = list(collection.find({"website": ObjectId('66ca13d8bba544259919833a')}, { "title": 1, "mileage": 1, "_id": 0 }))
titles = []
mileages = []

for d in listing_docs:
    if d.get('title') and d.get('mileage'):
        titles.append(d.get('title'))
        mileages.append(d.get('mileage'))

waiting_count = 0

# # Load pre-trained model (fine-tuned for car detection)
# model = EfficientNetB0(weights='imagenet')

# def preprocess_image(image_url):
#     response = requests.get(image_url)
#     img = Image.open(BytesIO(response.content))
#     img = img.resize((224, 224))
#     img_array = image.img_to_array(img)
#     img_array = np.expand_dims(img_array, axis=0)
#     img_array = tf.keras.applications.efficientnet.preprocess_input(img_array)
#     return img_array

# def extract_features(image_path):
#     img_array = preprocess_image(image_path)
#     features = model.predict(img_array, verbose=0)
#     return features.tolist()

def get_raw_data(soup):
    raw_values = {}

    for script in soup.find_all('script', type='text/javascript'):
        if 'if (!window[\'ngVdpModel\']) {\r\n        window[\'ngVdpModel\']' in script.text:
            json_string = script.text.strip()
            break

    # Updated pattern to capture the JSON assignment statement
    pattern = r"window\['([^']+)'\] = (\{.*);"
    matches = re.findall(pattern, json_string, re.DOTALL)

    for key, json_str in matches:
        # Trim JSON data up to the matching bracket
        bracket_count = 0
        for i, char in enumerate(json_str):
            if char == '{':
                bracket_count += 1
            elif char == '}':
                bracket_count -= 1
                # Stop when all opening brackets are matched
                if bracket_count == 0:
                    json_str = json_str[:i+1]
                    break

        try:
            # Attempt to parse the cleaned JSON string
            json_obj = json.loads(json_str)
            raw_values[key] = json_obj
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON for {key}: {e}")
            # Optionally handle or log the malformed JSON here

    return raw_values

def get_values(data):
    title = None
    description = None
    make = None
    model = None
    year = None
    mileage = None
    type = None
    vin = None
    zip_code = None
    fuel_type = None
    transmission = None
    cylinder = None
    engine = None
    color = None
    doors = None
    price = None
    features = None
    image_urls = None
    country = None
    city = None
    source = None
    type = None

    # views = None
    # likes = None
    # condition = None
    # driver_type = None
    # registration_status = None

    if data['ngVdpModel']['description']['description']:
        description = data['ngVdpModel']['description']['description'][0].get('description')

    title = data['ngVdpModel']['deepLinkSavedSearch']['savedSearch'].get('title')
    make = data['ngVdpModel']['hero'].get('make')
    model = data['ngVdpModel']['hero'].get('model')
    year = data['ngVdpModel']['hero'].get('year')
    mileage = data['ngVdpModel']['hero'].get('mileage')
    condition = data['ngVdpModel']['hero'].get('status')
    vin = data['ngVdpModel']['hero'].get('vin')
    zip_code = data['ngVdpModel']['ngIcoModel'].get('postalCode')
    price = data['ngVdpModel']['hero'].get('price')
    features = data['ngVdpModel']['featureHighlights'].get('highlights')
    image_urls = data['ngVdpModel']['gallery'].get('items')
    country = 'Canada'
    city = data['ngVdpModel']['deepLinkSavedSearch']['savedSearchCriteria'].get('city')
    source = 'autotrader.ca'
    # views = data['ngVdpModel'][''] # not found
    # likes = data['ngVdpModel'][''] # not found

    pattern = r"(?<=new & used )(.*?)(?= for sale within)"
    temp_title = re.search(pattern, title)
    if temp_title:
        title = temp_title.group(0).replace('vehicles ', '')

    if condition not in ["New", "Used"]:
        condition = None

    image_urls = [x['photoViewerUrl'] for x in image_urls]

    # # image_features = []
    # image_list = []
    # output_dir = "../public_html/assets/img/cars/"
    # new_id = ObjectId()

    # for i, image_doc in enumerate(image_urls):
    #     image_url = image_doc.get('photoViewerUrl')
    #     response = requests.get(image_url, timeout=10)
    #     response.raise_for_status()
    #     image_name = f"{str(new_id)+str(i)}.jpg"  # Save using the document's _id
    #     image_path = os.path.join(output_dir, image_name)

    #     if not os.path.exists(output_dir):
    #         os.makedirs(image_path) 

    #     # Save image to disk
    #     with open(image_path, 'wb') as file:
    #         file.write(response.content)

    #     image_list.append(f"https://autobrokerai.com/assets/img/cars/{image_name}")
    #     # try:
    #     #     image_features.append(extract_features(image_url))
    #     # except:
    #     #     print('Cannot extract feature:', image_url)

    for specs in data['ngVdpModel']['specifications']['specs']:
        if specs['key'] == 'Body Type':
            type = specs['value']
        # if specs['key'] == 'condition': # not found
        #     condition = specs['value']
        if specs['key'] == 'Fuel Type':
            fuel_type = specs['value']
        # if specs['key'] == 'driverType': # not found
        #     driver_type = specs['value']
        if specs['key'] == 'Transmission':
            transmission = specs['value']
        if specs['key'] == 'Cylinder':
            cylinder = specs['value']
        if specs['key'] == 'Engine': # type and name changed
            engine = specs['value']
        # if specs['key'] == 'registrationStatus': # not found
        #     registration_status = specs['value']
        if specs['key'] == 'Exterior Colour':
            color = specs['value']
        if specs['key'] == 'Doors':
            doors = specs['value']

    return {
        'title': title,
        'description': description,
        'make': make,
        'model': model,
        'year': int(year),
        'mileage': mileage,
        'bodyType': type,
        'condition': condition,
        'assembly': None, # Not found
        'vin': vin,
        'zipCode': zip_code,
        # 'fuelType': # hamza said not using
        "driverType": None, # Not found
        'transmission': transmission,
        'cylinder': int(cylinder),
        'engineSize': engine,
        'engineType': fuel_type,
        'registrationStatus': None, # Not found
        'color': color,
        'doors': doors,
        'seats': None, # Not found
        'price': int(price.replace(',', '')),
        'features': features,
        'imageUrls': image_urls,
        # 'imageFeatures': image_features,
        'country': country,
        'city': city,
        'website': 'AutoTrader',
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
    }

def recursive_try(link):
    global waiting_count
    product_req = requests.get(link, headers=headers)
    product_soup = BeautifulSoup(product_req.content, 'html.parser')
    
    if waiting_count < 5:
        if len(product_soup.text) < 100:
            waiting_count += 1
            print('Waiting...')
            time.sleep(15*60)
            product_soup, product_req.content = recursive_try(link)
        
        return product_soup, product_req.content
    else:
        return None

def get_id(collection, field_value):
    
    if field_value.get('name'):
        doc = collection.find_one(field_value)

        if doc:
            return doc['_id']
        else:
            result = collection.insert_one(field_value)
            return result.inserted_id
    else:
        return None
    
def upload_data(data):
    data['make'] = get_id(make_collection, {'name': data['make']})
    data['model'] = get_id(model_collection, {'name': data['model']})
    data['mileage'] = int(re.sub(r'[^\d]', '', data['mileage']))
    data['bodyType'] = get_id(body_type_collection, {'name': data['bodyType']})
    data['condition'] = get_id(condition_collection, {'name': data['condition']})
    data['transmission'] = get_id(transmission_collection, {'name': data['transmission']})
    data['engineType'] = get_id(engine_type_collection, {'name': data['engineType']})
    data['color'] = get_id(color_collection, {'name': data['color']})
    data['doors'] = int(re.sub(r'[^\d]', '', data['doors']))
    data['website'] = get_id(website_collection, {'name': data['website']})
    data['package'] = get_id(package_collection, {'name': data['package']})
    data['userId'] = get_id(user_id_collection, {'name': data['userId']})

    return data

break_flag = False

for i in list(range(0, 1000, 100)):
# for i in list(range(int(sys.argv[1]), 0, -100)):

    print("Index:", i)
    documents = []
    req = requests.get(f'https://www.autotrader.ca/cars/?rcp=100&rcs={i}&srt=35&prx=-1&loc=K0E%200B2&hprc=True&wcp=True&inMarket=advancedSearch', headers=headers)
    soup = BeautifulSoup(req.content, 'html.parser')

    main_listing_div = soup.find('div', id='SearchListings')
    listing_divs = soup.find_all('div', attrs={'class': 'dealer-split-wrapper'})

    for listing_div in listing_divs:
        link = 'https://www.autotrader.ca/' + listing_div.find('a', attrs={'class': 'inner-link'}).get('href')

        print('Link:', link)

        try:

            product_soup, content = recursive_try(link)

            if product_soup:

                waiting_count = 0

                raw_data = get_raw_data(product_soup)

                structured_data = get_values(raw_data)

                if structured_data['title'] in titles and structured_data['mileage'] in mileages:
                    print('Duplicate listing:', {structured_data['title']})
                    break_flag = True
                    break

                doc = upload_data(structured_data)

                doc['source'] = link

                documents.append(doc)
            else:
                break_flag = True
                break

        except:
            print("Skipping Link:", link)
        
    if break_flag:
        print("Ending...")
        break
    
    if documents:
        result = collection.insert_many(documents)
        print("length: ", len(documents))
    else:
        print("No result found.")

    # with open(f'data/page_{i}.json', 'w') as json_file:
    #     json.dump(documents, json_file, indent=4)