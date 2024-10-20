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
        response_format=MakeModelResponse,
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
    year: Optional[int]
    vin: Optional[str]
    car_type: Optional[str]
    mileage: Optional[int]
    description: Optional[str]
    condition: Optional[str]
    fuel_type: Optional[str]
    cylinder: Optional[str]
    engine_size: Optional[str]
    registration_status: Optional[str]
    color: Optional[str]
    num_doors: Optional[int]
    preferred_sell_price: Optional[float]
    features: Optional[List[str]]

# Define the structure for the response
class CarDetailsResponse(BaseModel):
    car_details: Optional[CarDetails]
    error: Optional[str]

# Helper function to save uploaded files temporarily
async def save_image(image: UploadFile, filename: str) -> str:
    file_path = f"/tmp/{filename}"
    async with aiofiles.open(file_path, 'wb') as out_file:
        while content := await image.read(1024):
            await out_file.write(content)
    return file_path

# Route to process uploaded images and extract car information
@app.post("/extract-car-details/", response_model=CarDetailsResponse)
async def extract_car_details(
    front_image: UploadFile = File(...),
    back_image: UploadFile = File(...),
    right_side_image: UploadFile = File(...),
    left_side_image: UploadFile = File(...),
    interior_image: UploadFile = File(...),
    damage_part_image: Optional[UploadFile] = None,
    special_option_image: Optional[UploadFile] = None
):
    # Save the uploaded images
    front_image_path = await save_image(front_image, "front_image.jpg")
    back_image_path = await save_image(back_image, "back_image.jpg")
    right_side_image_path = await save_image(right_side_image, "right_side_image.jpg")
    left_side_image_path = await save_image(left_side_image, "left_side_image.jpg")
    interior_image_path = await save_image(interior_image, "interior_image.jpg")
    
    damage_part_image_path = await save_image(damage_part_image, "damage_part_image.jpg") if damage_part_image else None
    special_option_image_path = await save_image(special_option_image, "special_option_image.jpg") if special_option_image else None

    # Prepare the prompt for GPT-4 Vision
    vision_prompt = f"""
    I have uploaded images of a car. Extract the following information from the images:
    - Make
    - Model
    - Year
    - VIN
    - Car type
    - Mileage
    - Description
    - Condition
    - Fuel type
    - Number of cylinders
    - Engine size
    - Registration status
    - Color
    - Number of doors
    - Preferred sell price (in USD)
    - Features (such as sunroof, navigation system, etc.)
    
    The images are as follows:
    - Front view: {front_image_path}
    - Back view: {back_image_path}
    - Right side view: {right_side_image_path}
    - Left side view: {left_side_image_path}
    - Interior: {interior_image_path}
    """
    if damage_part_image_path:
        vision_prompt += f"\n- Damage part (optional): {damage_part_image_path}"
    if special_option_image_path:
        vision_prompt += f"\n- Special option part (optional): {special_option_image_path}"

    try:
        # Use GPT-4 Vision to analyze the images and extract information
        completion = openai_client.beta.chat.completions.create(
            model="gpt-4-vision-2024",
            messages=[
                {"role": "system", "content": "You are an assistant that helps extract car information from images."},
                {"role": "user", "content": vision_prompt}
            ]
        )

        # Extract the parsed information
        message = completion.choices[0].message.content

        # Parse the extracted car details from GPT-4 Vision response
        car_details = {
            # You would parse the details accordingly from the response here
            "make": message.get("Make"),
            "model": message.get("Model"),
            "year": message.get("Year"),
            "vin": message.get("VIN"),
            "car_type": message.get("Car type"),
            "mileage": message.get("Mileage"),
            "description": message.get("Description"),
            "condition": message.get("Condition"),
            "fuel_type": message.get("Fuel type"),
            "cylinder": message.get("Number of cylinders"),
            "engine_size": message.get("Engine size"),
            "registration_status": message.get("Registration status"),
            "color": message.get("Color"),
            "num_doors": message.get("Number of doors"),
            "preferred_sell_price": message.get("Preferred sell price"),
            "features": message.get("Features")
        }

        return CarDetailsResponse(car_details=CarDetails(**car_details))
    
    except Exception as e:
        return CarDetailsResponse(error=f"Failed to extract car details: {str(e)}")
