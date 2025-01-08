import re
import json
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from pymongo import MongoClient

with open('credential.json') as json_file:
    conn_data = json.load(json_file)
conn_string = conn_data['mongo_conn_string']

client = MongoClient(conn_string)
db = client['test']

review_collection = db['reviews']
make_collection = db['makes']
model_collection = db['models']
makess = list(make_collection.find({}, { "name": 1 }))
models = list(model_collection.find({}, { "name": 1 }))

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

make_res = requests.get("https://www.topgear.com/api/search/CarReviews?fields%5BCarReviews%5D=url%2Ctitle&filter%5Bmake%5D")
make_data = make_res.json()

make_list = [d['key'] for d in make_data['meta']['facets']['make']]

documents = []

for make in make_list:
    res = requests.get("https://www.topgear.com/api/search/CarReviews?fields%5BCarReviews%5D=url%2Ctitle&filter%5Bmake%5D=" + make)
    data = res.json()

    make = make.title()

    urls = [[d['attributes']['title'], 'https://www.topgear.com' + d['attributes']['url']] for d in data['data']]

    for url in urls:
        model = url[0].replace(make, '').strip()

        res = requests.get(url[1])
        soup = BeautifulSoup(res.content, 'html.parser')

        title = soup.find('h1', attrs={'data-testid': 'Canon'}).text
        releaseDate = soup.find('span', attrs={'class': 'sc-brKeYL CreatedDate-sc-10pl2l7-5 cAsxkv cTCKck'}).text
        try:
            price = soup.find('div', attrs={'class': 'sc-beqWaB dGitLJ'}).find('span', attrs={'data-testid': 'PriceText'}).text
        except:
            pass
        overview = soup.find('div', attrs={'class': 'sc-beqWaB sc-fmSAUk djcJsJ'}).find('p').text
        description_tags = soup.find('div', attrs={'class': 'sc-beqWaB sc-fmSAUk djcJsJ'}).find_all('p')
        description = [p.text for p in description_tags[1:]]
        imageUrl = 'https://www.topgear.com' +  soup.find('img', attrs={'class': 'image-gallery-image'}).get('src')
        spec_res = requests.get(url[1]+'/specs')
        spec_soup = BeautifulSoup(spec_res.content, 'html.parser')
        specs_rows = spec_soup.find('table', attrs={'role': 'table'})
        if specs_rows:
            headings = specs_rows.find_all('th')
            headings = [h.text for h in headings]

            for row in specs_rows.find_all('tr'):
                columns = row.find_all('td')
                specs = [col.text for col in columns]
                if specs:
                    break
            for i, heading in enumerate(headings):
                if heading == '0-62':
                    zeroToHundred = specs[i]
                if heading == 'BHP':
                    maxPower = specs[i] + ' bhp'

        documents.append({
            'title': title,
            'description': description,
            'overview': overview,
            'make': get_id('makess', make),
            'model': get_id('models', model),
            'releaseDate': datetime.strptime(releaseDate.replace('Published: ', '').strip(), '%d %b %Y'),
            'bodyType': None,
            'transmission': None, 
            'engineSize': None,
            'engineType': None,
            'fuelConsumption': None, 
            'price': get_int(price),
            'maxPower': maxPower,
            'maxTorque': None,
            'zeroToHundred': float(zeroToHundred.replace('s', '')) if zeroToHundred else None,
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