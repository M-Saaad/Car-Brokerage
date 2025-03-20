import re
import json
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from pymongo import MongoClient

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

review_collection = db['reviews']
make_collection = db['makes']
model_collection = db['models']
body_type_collection = db['bodytypes']
transmission_collection = db['transmissions']
engine_type_collection = db['enginetypes']

package_collection = db['packages']
user_id_collection = db['users']
color_collection = db['colors']
website_collection = db['websites']
condition_collection = db['conditions']
driver_type_collection = db['drivertypes']
fuel_type_collection = db['fueltypes']
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

make_model_dict = {}

makes = list(make_collection.find({}, {"_id": 1, "name": 1}))

for make in makes:
    make_id = make["_id"]
    make_name = make["name"]

    models = list(model_collection.find({"make": make_id}, {"_id": 0, "name": 1}))
    model_names = [model["name"] for model in models]

    make_model_dict[make_name] = model_names

res = requests.get("https://www.motortrend.com/car-reviews", headers=headers)

sub_soup = BeautifulSoup(res.content, 'html.parser')

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

def get_int(string):
    try:
        return int(re.sub(r'[^\d]', '', string))
    except:
        return None
    
make_list = []
documents = []

for make_anchor in sub_soup.find('section', attrs={'aria-labelledby': ':S2:'}).find_all('a'):
    make = make_anchor.find('div', attrs={'class': 'flex w-full flex-col gap-1'}).find('p').text
    make_res = requests.get("https://www.motortrend.com" + make_anchor.get('href'), headers=headers)
    make_soup = BeautifulSoup(make_res.content, 'html.parser')

    try:
        make_soup.find('div', attrs={'class': 'grid grid-flow-row grid-cols-1'}).find_all('a')
    except:
        continue

    for model_anchor in make_soup.find('div', attrs={'class': 'grid grid-flow-row grid-cols-1'}).find_all('a'):
        title = None
        description = None
        overview = None
        model = None
        releaseDate = None
        transmission = None
        engineSize = None
        fuelConsumption = None
        price = None
        maxPower = None
        maxTorque = None
        zeroToHundred = None
        imageUrl = None

        model_res = requests.get('https://www.motortrend.com' + model_anchor.get('href'), headers=headers)
        model_soup = BeautifulSoup(model_res.content, 'html.parser')

        print('Url:', 'https://www.motortrend.com' + model_anchor.get('href'))

        try:
            for m in make_model_dict[make]:
                if " " + m in model_soup.find('p', attrs={'class': 'transition-colors motion-reduce:transition-none typography-body2 text-neutral-2 dark:text-neutral-6'}).text:
                    model = m
        except:
            pass

        if not model:
            break

        try:
            title = model_soup.find('h1', attrs={'data-ids': 'Typography'}).text
        except:
            pass
        try:
            overview = model_soup.find('div', attrs={'class', 'flex flex-col gap-8 md:gap-12'}).find('p').text
        except:
            pass
        try:
            releaseDate = model_soup.find('time').text
            releaseDate = datetime.strptime(releaseDate, '%b %d, %Y')
        except:
            pass
        try:
            description = model_soup.find('div', attrs={'class', 'flex flex-col gap-8 md:gap-12'}).find_all('p', attrs={'data-component': 'TextElement'})
        except:
            pass
        try:
            description = [d.text for d in description]
        except:
            pass
        
        try:
            for tr in model_soup.find('tbody', attrs={'data-ids': 'TableBody'}).find_all('tr', attrs={'data-ids': 'TableRow'}):
                spec = tr.find_all('td', attrs={'data-ids': 'TableCell'})
                if spec[0].text == 'TRANSMISSION':
                    transmission = spec[1].text
                if spec[0].text == 'ENGINE' or spec[0].text == 'MOTOR TYPE':
                    engineSize = spec[1].text
                if spec[0].text == 'EPA CITY/HWY/COMB FUEL ECON':
                    fuelConsumption = spec[1].text
                if spec[0].text == 'BASE PRICE':
                    price = spec[1].text
                if spec[0].text == 'POWER (SAE NET)':
                    maxPower = spec[1].text
                if spec[0].text == 'TORQUE (SAE NET)':
                    maxTorque = spec[1].text
                if spec[0].text == '0-60 MPH':
                    zeroToHundred = round(float(spec[1].text.replace(' sec', '')) * (100 / (60 * 1.60934)), 2)
        except:
            pass
        
        try:
            imageUrl = model_soup.find('div', attrs={'data-component': 'ImageElement'}).find('img').get('src')
        except:
            pass

        if imageUrl:
            documents.append({
                'title': title,
                'description': description,
                'overview': overview,
                'make': get_id('makess', make),
                'model': get_id('models', model),
                'releaseDate': releaseDate,
                'bodyType': None,
                'transmission': get_id('transmissions', transmission), 
                'engineSize': get_id('engine_types', engineSize),
                'engineType': None,
                'fuelConsumption': fuelConsumption, 
                'price': get_int(price),
                'maxPower': maxPower,
                'maxTorque': maxTorque,
                'zeroToHundred': zeroToHundred,
                'imageUrl': imageUrl, 
                'fiveStar': None,
                'fourStar': None,
                'threeStar': None, 
                'twoStar': None,
                'oneStar': None,
                'analytics': None,
                "createdAt": datetime.now(),
                "updatedAt": datetime.now()
            })

if documents:
    listing_result = review_collection.insert_many(documents)
    print("length: ", len(documents))
        