from pymongo import MongoClient, UpdateOne
import requests
from collections.abc import Iterable
import json
from datetime import datetime

# Load MongoDB credentials
with open("credential.json") as json_file:
    conn_data = json.load(json_file)
conn_string = conn_data["mongo_conn_string"]

# MongoDB connection
client = MongoClient(conn_string)
db = client["test"]
listing_collection = db["listings"]
websites_collection = db["websites"]

# Request headers
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}

def is_valid_url(urls):
    """Checks if a URL (or list of URLs) is valid and reachable."""
    if isinstance(urls, str):
        urls = [urls]
    elif not isinstance(urls, Iterable):
        return False

    for url in urls:
        try:
            # response = requests.get(url, allow_redirects=True, headers=HEADERS, timeout=5)
            response = requests.head(url, allow_redirects=True, headers=HEADERS, timeout=2)
            if response.status_code != 200:
                return False
        except requests.RequestException:
            return False
    return True

def get_website_name(website_id):
    """Fetches the name field of a website from websites_collection using ObjectId."""
    website_entry = websites_collection.find_one({"_id": website_id}, {"name": 1})
    return website_entry["name"] if website_entry else None

def get_updated_entries():
    """Fetches entries, validates URLs, and updates entries in bulk."""
    bulk_updates = []
    invalid_ids = []
    
    # Fetch entries where "invalid" does not exist
    listings = list(listing_collection.find(
        {"invalid": {"$exists": False}}, 
        {"source": 1, "price": 1, "imageUrls": 1, "website": 1, "_id": 1}
    ))

    # for entry in listings:
    #     source = entry.get("source")
    #     image_urls = entry.get("imageUrls")
    #     entry_id = entry["_id"]

    #     souce_valid = is_valid_url(source)
    #     images_valid = is_valid_url(image_urls)

    #     if not souce_valid or not images_valid:
    #         bulk_updates.append(UpdateOne({"_id": entry_id}, {"$set": {"invalid": True}}))
    #         print(f"Marked entry {entry_id} as invalid (source: {souce_valid}, image: {images_valid})")

    # # Perform bulk update in MongoDB
    # if bulk_updates:
    #     listing_collection.bulk_write(bulk_updates)
    #     print(f"Bulk updated {len(bulk_updates)} entries.")

    try:
        with open("update_logs.json") as json_file:
            logs = json.load(json_file, indent=4)
    except:
        logs = []

    # Gather IDs of documents with invalid URLs
    for entry in listings:
        source = entry.get("source")
        image_urls = entry.get("imageUrls")
        entry_id = entry["_id"]
        website_id = entry.get("website")
        website_text = get_website_name(website_id) if website_id else None

        souce_valid = is_valid_url(source)
        if souce_valid:
            images_valid = is_valid_url(image_urls)
        else:
            images_valid = None

        logs.append(
            {
                str(datetime.now()): {
                    entry_id: {
                        'website': website_text,
                        'souce_valid': souce_valid,
                        'images_valid': images_valid
                    }
                }
            }
        )

        if not souce_valid or not images_valid:
            invalid_ids.append(entry_id)
            print(f"Marked entry {entry_id} as invalid (website: {website_text} source: {souce_valid}, image: {images_valid}) IDX: {idx}")

        # Process invalid entries in chunks
        if len(invalid_ids) > 1000:
            result = listing_collection.update_many(
                {"_id": {"$in": invalid_ids}},
                {"$set": {"invalid": True}}
            )
            print(f"Bulk updated {result.modified_count} entries.")
            invalid_ids = []
    
    # # Perform bulk update using update_many if there are invalid entries
    # if invalid_ids:
    #     result = listing_collection.update_many(
    #         {"_id": {"$in": invalid_ids}},  # Filter by IDs that need to be updated
    #         {"$set": {"invalid": True}}  # Update invalid field to True
    #     )
    #     print(f"Bulk updated {result.modified_count} entries.")

    with open("update_logs.json", "w") as json_file:
        json.dump(logs, json_file, indent=4)

if __name__ == "__main__":
    get_updated_entries()
