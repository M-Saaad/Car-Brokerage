import os
import json
import requests
from bson import ObjectId
from pymongo import MongoClient

# MongoDB connection
with open('credential.json') as json_file:
    conn_data = json.load(json_file)
conn_string = conn_data['mongo_conn_string']
client = MongoClient(conn_string)
db = client['test']
collection = db['listings']

# Directory to save images
output_dir = "../public_html/assets/img/cars/"
os.makedirs(output_dir, exist_ok=True)

def download_and_update(entry):
    image_urls = entry.get('imageUrls')
    if not image_urls:
        return

    new_urls = []
    
    for i, image_url in enumerate(image_urls):
        try:
            # Download image
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            image_name = f"{str(entry['_id'])+str(i)}.jpg"  # Save using the document's _id
            image_path = os.path.join(output_dir, image_name)

            if not os.path.exists(output_dir):
                os.makedirs(image_path) 

            # Save image to disk
            with open(image_path, 'wb') as file:
                file.write(response.content)

            new_urls.append(f"https://autobrokerai.com/assets/img/cars/{image_name}")
        
        except Exception as e:
            print(f"Failed to process {image_url}: {e}")

    print("Updating:", str(entry['_id']))
    if new_urls:
        collection.update_one({'_id': entry['_id']}, {'$set': {'imageUrls': new_urls}})
    else:
        collection.update_one({'_id': entry['_id']}, {'$set': {'imageUrls': None}})

def main():
    while(True):
        try:
            # Fetch all documents with image URLs
            entries = collection.find({
                "imageUrls": {
                    "$elemMatch": {
                        "$not": {
                            "$regex": "^https://autobrokerai\\.com/"
                        }
                    }
                }
            })

            for entry in entries:
                download_and_update(entry)
        except:
            main()

if __name__ == "__main__":
    main()
