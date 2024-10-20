from typing import List, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from pymongo import MongoClient
from bson import ObjectId
from openai import OpenAI
import aiofiles
import rich
import json

# FastAPI app
app = FastAPI()

with open('credential.json') as json_file:
    conn_data = json.load(json_file)
conn_string = conn_data['mongo_conn_string']

client = MongoClient(conn_string)
db = client['test']
listing_collection = db['listings']
make_collection = db['makes']
model_collection = db['model']

# OpenAI API key
with open('credential.json') as json_file:
    cred_data = json.load(json_file)
api_key = cred_data['open_ai_key']
openai_client = OpenAI(api_key=api_key)

# Define the structure to hold car make, model, and year information
class MakeModelYear(BaseModel):
    make: str
    model: str
    year: int

# Define the structure for the API request
class CarRequest(BaseModel):
    query: str  # User's input query

# Modify the response structure
class MakeModelResponse(BaseModel):
    car_info: Optional[MakeModelYear]
    error: Optional[str]

@app.post("/prompt-search/")
async def search_listing(car_request: CarRequest):
    # Use OpenAI to extract car make, model, and year from the user's query
    completion = openai_client.beta.chat.completions.parse(
        model="gpt-4o-2024-08-06",
        messages=[
            {"role": "system", "content": "You are an assistant that extracts the make, model, and year of cars from user queries."},
            {"role": "user", "content": car_request.query},
        ],
        response_format=MakeModelResponse
    )

    # Process the OpenAI response
    message = completion.choices[0].message
    if message.parsed and message.parsed.car_info:
        make = message.parsed.car_info.make
        model = message.parsed.car_info.model
        year = message.parsed.car_info.year

        rich.print(f"Extracted: Make: {make}, Model: {model}, Year: {year}")

        # Query MongoDB
        # Step 1: Find the ObjectId for the make in make_collection
        make_doc = make_collection.find_one({"name": make})
        if not make_doc:
            raise HTTPException(status_code=404, detail=f"No matching make found for '{make}'")
        make_id = make_doc['_id']

        # Step 2: Find the ObjectId for the model in model_collection (matching the make_id)
        model_doc = model_collection.find_one({"name": model})
        if not model_doc:
            raise HTTPException(status_code=404, detail=f"No matching model found for '{model}' under make '{make}'")
        model_id = model_doc['_id']

        # Step 3: Query the listing_collection using the make_id, model_id, and year
        result = {
            "make": str(make_id),
            "model": str(model_id),
            "year": year
        }

        return result
    
    else:
        raise HTTPException(status_code=400, detail="Could not extract make, model, or year from the query.")

# Define the structure to hold the car's extracted information
class CarDetails(BaseModel):
    make: str
    model: str
    year: int
    vin: Optional[str]
    type: Optional[str]
    mileage: Optional[int]
    description: str
    condition: Optional[str]
    fuel_type: Optional[str]
    cylinder: Optional[str]
    engine_size: Optional[str]
    registration_status: Optional[str]
    color: Optional[str]
    doors: Optional[int]
    price: float
    features: Optional[List[str]]

# Define the structure for the response
class CarDetailsResponse(BaseModel):
    car_details: Optional[CarDetails]
    error: Optional[str]

# Define the structure for the request
class CarDetailsRequest(BaseModel):
    front_image: str
    back_image: str
    right_side_image: str
    left_side_image: str
    interior_image: str
    damage_part_image: Optional[str]
    special_option_image: Optional[str]

# Helper function to save uploaded files temporarily
async def save_image(image: UploadFile, filename: str) -> str:
    file_path = f"/tmp/{filename}"
    async with aiofiles.open(file_path, 'wb') as out_file:
        while content := await image.read(1024):
            await out_file.write(content)
    return file_path

# Route to process uploaded images and extract car information
@app.post("/extract-car-details/", response_model=CarDetailsResponse)
async def extract_car_details(car_detail_request: CarDetailsRequest):
    # Save the uploaded images
    # front_image_path = await save_image(front_image, "front_image.jpg")
    # back_image_path = await save_image(back_image, "back_image.jpg")
    # right_side_image_path = await save_image(right_side_image, "right_side_image.jpg")
    # left_side_image_path = await save_image(left_side_image, "left_side_image.jpg")
    # interior_image_path = await save_image(interior_image, "interior_image.jpg")
    
    # damage_part_image_path = await save_image(damage_part_image, "damage_part_image.jpg") if damage_part_image else None
    # special_option_image_path = await save_image(special_option_image, "special_option_image.jpg") if special_option_image else None

    # Prepare the prompt for GPT-4 Vision
    vision_prompt = f"""
    I have uploaded images of a car. Extract the following information from the images:
    - Make
    - Model
    - Year
    - VIN
    - Car type
    - Mileage
    - Description (breif description for selling post)
    - Condition (analyzed condition from images)
    - Fuel type
    - Number of cylinders
    - Engine size
    - Registration status
    - Color
    - Number of doors
    - Price (suggested selling price in usd)
    - Features (such as sunroof, navigation system, etc.)
    
    The images you will get in following sequence:
    - Front view:
    - Back view:
    - Right side view:
    - Left side view:
    - Interior:
    - Damage part (optional):
    - Special option part (optional):
    """

    content = [
        {"type": "text", "text": vision_prompt},
        {
            "type": "image_url",
            "image_url": {
                "url": car_detail_request.front_image,
                "detail": "low"
            },
        },
        {
            "type": "image_url",
            "image_url": {
                "url": car_detail_request.back_image,
                "detail": "low"
            },
        },
        {
            "type": "image_url",
            "image_url": {
                "url": car_detail_request.right_side_image,
                "detail": "low"
            },
        },
        {
            "type": "image_url",
            "image_url": {
                "url": car_detail_request.left_side_image,
                "detail": "low"
            },
        },
        {
            "type": "image_url",
            "image_url": {
                "url": car_detail_request.interior_image,
                "detail": "low"
            },
        }
    ]

    if car_detail_request.damage_part_image:
        content.append({
            "type": "image_url",
            "image_url": {
                "url": car_detail_request.damage_part_image,
                "detail": "low"
            },
        })
    if car_detail_request.special_option_image:
        content.append({
            "type": "image_url",
            "image_url": {
                "url": car_detail_request.special_option_image,
                "detail": "low"
            },
        })

    # try:
    # Use GPT-4 Vision to analyze the images and extract information
    completion = openai_client.beta.chat.completions.parse(
        model="gpt-4o-2024-08-06",
        messages=[
            {
                "role": "system",
                "content": "You are an assistant that helps extract car information from images."
            },
            {
                "role": "user",
                "content": content
            }
        ],
        response_format=CarDetailsResponse
    )


    # Extract the parsed information
    message = completion.choices[0].message

    if message.parsed:

        # Parse the extracted car details from GPT-4 Vision response
        car_details = {
            # You would parse the details accordingly from the response here
            "make": message.parsed.car_details.make,
            "model": message.parsed.car_details.model,
            "year": message.parsed.car_details.year,
            "vin": message.parsed.car_details.vin,
            "type": message.parsed.car_details.type,
            "mileage": message.parsed.car_details.mileage,
            "description": message.parsed.car_details.description,
            "condition": message.parsed.car_details.condition,
            "fuel_type": message.parsed.car_details.fuel_type,
            "cylinder": message.parsed.car_details.cylinder,
            "engine_size": message.parsed.car_details.engine_size,
            "registration_status": message.parsed.car_details.registration_status,
            "color": message.parsed.car_details.color,
            "doors": message.parsed.car_details.doors,
            "price": message.parsed.car_details.price,
            "features": message.parsed.car_details.features
        }

        return CarDetailsResponse(car_details=CarDetails(**car_details), error=None)
        
    # except Exception as e:
    #     return CarDetailsResponse(car_details=None, error=f"Failed to extract car details: {str(e)}")
