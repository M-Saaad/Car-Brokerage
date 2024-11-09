import re
import json
import requests
from datetime import datetime
from pymongo import MongoClient
from bson.objectid import ObjectId

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

listing_docs = list(listing_collection.find({"website": ObjectId('672f45993b775f8c9cfa9241')}, { "title": 1, "mileage": 1, "_id": 0 }))
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
    if data:
        for doc in data['inventory']:
            title = ' '.join(doc.get('title'))
            if title in titles and mileage in mileages:
                print("Skipping!!!")
                break
            
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
                'imageUrls': [img['uri'] for img in doc['images']],
                'country': 'United States',
                'city': city if city else None,
                'website': 'Avis Car Sales',
                'source': 'https://www.aviscarsales.com' + doc.get('link'),
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
    url = f"https://www.aviscarsales.com/apis/widget/INVENTORY_LISTING_DEFAULT_AUTO_USED:inventory-data-bus1/getInventory?geoZip=&geoRadius=0&start={count}"
    res = requests.get(url)
    
    if res.status_code == 200:
        res_data = res.json()
        listing_documents.extend(get_raw_data(res.json()))
    else:
        print("Status code 200 for link:", url)
    
    count += 18

    if count > res_data['pageInfo']['totalCount']:
        break

if listing_documents:
    listing_result = listing_collection.insert_many(listing_documents)
    print("length: ", len(listing_documents))