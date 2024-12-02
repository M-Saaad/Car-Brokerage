import re
import os
import json
import requests
from datetime import datetime
from pymongo import MongoClient
from bson.objectid import ObjectId

import requests

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.6723.116 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
}

# Payload data
payload = {
    "siteId": "hertzcarsales",
    "locale": "en_US",
    "device": "DESKTOP",
    "flags": {
        "vcda-js-environment": "live",
        "ws-scripts-concurrency-limits-concurrency": 16,
        "ws-scripts-concurrency-limits-enabled": True,
        "ws-scripts-concurrency-limits-queue": 16,
        "ws-scripts-inline-css": True,
        "enable-account-data-distributor-fetch-ws-inv-data": False,
        "enable-client-side-geolocation-ws-inv-data": False,
        "srp-test-package-data": 0,
        "srp-track-fetch-resource-timing": False,
        "ws-inv-data-fetch-retries": 2,
        "ws-inv-data-fetch-timeout": 5000,
        "ws-inv-data-location-service-fetch-retries": 2,
        "ws-inv-data-location-service-fetch-timeout": 3000,
        "ws-inv-data-preload-inventory": True,
        "ws-inv-data-spellcheck-proxy-timeout": 5000,
        "ws-inv-data-spellcheck-server-retries": 0,
        "ws-inv-data-spellcheck-server-timeout": 1500,
        "ws-inv-data-use-wis": True,
        "ws-inv-data-wis-fetch-timeout": 5000,
        "ws-itemlist-model-version": "v1",
        "ws-itemlist-service-version": "v5",
        "wsm-account-data-distributor-retries": 2,
        "wsm-account-data-distributor-timeout": 50
    },
    "includePricing": True,
    "inventoryParameters": {
        "geoRadius": ["0"],
        "geoZip": [""],
        "start": ["0"]
    },
    "pageAlias": "INVENTORY_LISTING_GRID_AUTO_ALL",
    "pageId": "hertzcarsales_SITEBUILDER_INVENTORY_SEARCH_RESULTS_AUTO_USED_V1_196",
    "widgetName": "ws-inv-data",
    "windowId": "inventory-data-bus1"
}

with open('credential.json') as json_file:
    conn_data = json.load(json_file)
conn_string = conn_data['mongo_conn_string']

client = MongoClient(conn_string)
db = client['test']
listing_collection = db['listings']
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

listing_docs = list(listing_collection.find({"website": ObjectId('672f377ed2b0a68386cdf184')}, { "title": 1, "mileage": 1, "_id": 0 }))
titles = []
mileages = []

for d in listing_docs:
    if d.get('title') and d.get('mileage'):
        titles.append(d.get('title'))
        mileages.append(d.get('mileage'))

def get_int(string):
    try:
        return int(re.sub(r'[^\d]', '', string))
    except:
        return None

count = 0

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

def get_raw_data(data):
    listing_documents = []
    if data.get('inventory'):
        for doc in data['inventory']:
            title = ' '.join(doc.get('title'))

            mileage = None
            engine = None
            transmission = None
            color = None
            city = None
            for attr in doc['attributes']:
                if attr['name'] == 'odometer' and attr['label'] == 'Mileage':
                    mileage = get_int(attr['value'])
                if attr['name'] == 'engine' and attr['label'] == 'Engine':
                    engine = attr['value']
                if attr['name'] == 'transmission' and attr['label'] == 'Transmission':
                    transmission = attr['value']
                if attr['name'] == 'exteriorColor' and attr['label'] == 'Exterior Color':
                    color = attr['value']
                if attr['name'] == 'accountName' and attr['label'] == 'Location':
                    city = attr['value'].replace('Avis ', '').replace('Car Sales ', '').strip()

            if title in titles and mileage in mileages:
                print("Skipping!!!")
                break

            image_list = []
            output_dir = "../public_html/assets/img/cars/"
            new_id = ObjectId()

            for i, img in enumerate([img['uri'] for img in doc['images']]):
                response = requests.get(img, timeout=10)
                response.raise_for_status()
                image_name = f"{str(new_id)+str(i)}.jpg"  # Save using the document's _id
                image_path = os.path.join(output_dir, image_name)

                # Save image to disk
                with open(image_path, 'wb') as file:
                    file.write(response.content)

                image_list.append(f"https://autobrokerai.com/assets/img/cars/{image_name}")

            listing_documents.append(upload_data({
                'title': title,
                'description': None,
                'make': doc.get('make'),
                'model': doc.get('model'),
                'year': doc.get('year'),
                'mileage': mileage if mileage else None,
                'bodyType': doc.get('bodyStyle'),
                'condition': 'Used',
                'assembly': None,
                'vin': doc.get('vin'),
                'zipCode': None,
                'driverType': None,
                'transmission': transmission if transmission else None,
                'cylinder': None,
                'engineSize': engine if engine else None,
                'engineType': doc.get('fuelType'),
                'registrationStatus': None,
                'color': color if color else None,
                'doors': None,
                'seats': None,
                'price': get_int(doc.get('pricing')['retailPrice']) if doc.get('pricing') else None,
                'features': None,
                'imageUrls': image_list,
                'country': 'United States',
                'city': city if city else None,
                'website': 'Hertz Car Sales',
                'source': 'https://www.hertzcarsales.com' + doc.get('link'),
                'views': 0,
                'likes': 0,
                'status': 'Active',
                'cpePick': False,
                'soldThrough': None, # Dont know,
                'package': 'Free',
                'userId': "Admin 1",
                'createdAt': datetime.now(),
                'updatedAt': datetime.now()
            }))
        
        return listing_documents
            
    else:
        print("No inventory for link:", url)

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

listing_documents = []

while (True):
    url = "https://www.hertzcarsales.com/api/widget/ws-inv-data/getInventory"
    payload['inventoryParameters']['start'] = [str(count)]
    res = requests.post(url, json=payload)
    
    if res.status_code == 200:
        res_data = res.json()
        listing_documents.extend(get_raw_data(res_data))
    else:
        print("Status code 200 for link:", url)
    
    count += 18

    if count > res_data['pageInfo']['totalCount']:
        break

if listing_documents:
    listing_result = listing_collection.insert_many(listing_documents)
    print("length: ", len(listing_documents))