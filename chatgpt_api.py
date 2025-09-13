from typing import List, Optional
from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pymongo import MongoClient
from openai import OpenAI
import aiofiles
import json

# FastAPI app
app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins. Change to specific domains for more control.
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods
    allow_headers=["*"],  # Allows all headers
)

with open('credential.json') as json_file:
    conn_data = json.load(json_file)
conn_string = conn_data['mongo_conn_string']

client = MongoClient(conn_string)
db = client['test']
listing_collection = db['listings']
auctions_collection = db['auctions']
make_collection = db['makes']
model_collection = db['models']
bodyType_collection = db['bodytypes']
condition_collection = db['conditions']
assembly_collection = db['assemblies']
driverType_collection = db['drivertypes']
transmission_collection = db['transmission']
engineType_collection = db['enginetypes']
color_collection = db['colors']
website_collection = db['website']

countries = listing_collection.distinct("country")

make_list = list(make_collection.find({}, { 'name': 1 }))
model_list = list(model_collection.find({}, { 'name': 1 }))
bodyType_list = list(bodyType_collection.find({}, { 'name': 1 }))
condition_list = list(condition_collection.find({}, { 'name': 1 }))
assembly_list = list(assembly_collection.find({}, { 'name': 1 }))
driverType_list = list(driverType_collection.find({}, { 'name': 1 }))
transmission_list = list(transmission_collection.find({}, { 'name': 1 }))
engineType_list = list(engineType_collection.find({}, { 'name': 1 }))
color_list = list(color_collection.find({}, { 'name': 1 }))
website_list = list(website_collection.find({}, { 'name': 1 }))
color_str_list = [c['name'] for c in color_list]

# OpenAI API key
with open('credential.json') as json_file:
    cred_data = json.load(json_file)
api_key = cred_data['open_ai_key']
openai_client = OpenAI(api_key=api_key)

def get_id(col_name, field_value):
    result = None
    global makess
    global models
    global make_list
    global model_list
    global bodyType_list
    global condition_list
    global assembly_list
    global driverType_list
    global transmission_list
    global engineType_list
    global color_list
    global website_list
    
    if field_value:
        if col_name == 'make':
            col_list = make_list
        elif col_name == 'model':
            col_list = model_list
        elif col_name == 'bodyType':
            col_list = bodyType_list
        elif col_name == 'condition':
            col_list = condition_list
        elif col_name == 'assembly':
            col_list = assembly_list
        elif col_name == 'driverType':
            col_list = driverType_list
        elif col_name == 'transmission':
            col_list = transmission_list
        elif col_name == 'engineType':
            col_list = engineType_list
        elif col_name == 'color':
            col_list = color_list
        elif col_name == 'website':
            col_list = website_list

        for doc in col_list:
            if doc.get('name') == field_value:
                result = doc
                break
        
        if result:
            return str(result.get('_id'))

        else:
            if col_name == 'make':
                result = make_collection.insert_one({'name': field_value})
                makess = list(make_collection.find({}, { "name": 1 }))
                return result.inserted_id
            elif col_name == 'model':
                result = model_collection.insert_one({'name': field_value})
                models = list(model_collection.find({}, { "name": 1 }))
                return result.inserted_id
            return None
    
    else:
        return None

# Define the structure to hold the car's extracted information
class SearchCarDetails(BaseModel):
    make: Optional[str]
    model: Optional[str]
    year_from: Optional[int]
    year_to: Optional[int]
    mileage_from: Optional[int]
    mileage_to: Optional[int]
    bodyType: Optional[str]
    condition: Optional[str]
    assembly: Optional[str]
    driverType: Optional[str]
    transmission: Optional[str]
    cylinder: Optional[int]
    engineSize: Optional[str]
    engineType: Optional[str]
    registrationStatus: Optional[bool]
    color: Optional[str]
    expandColors: Optional[List[str]]
    doors: Optional[int]
    seats: Optional[int]
    price_from: Optional[int]
    price_to: Optional[int]
    country: Optional[str]
    city: Optional[str]
    website: Optional[str]
    features: Optional[List[str]]

# Define the structure for the response
class SearchCarDetailsResponse(BaseModel):
    car_details: Optional[SearchCarDetails]
    error: Optional[str]

# Define the structure for the API request
class SearchCarRequest(BaseModel):
    query: str

# Define the structure to hold the car's extracted information
class ImageCarDetails(BaseModel):
    make: str
    model: str
    title: Optional[str]
    description: Optional[str]
    year: Optional[int]
    bodyType: Optional[str]
    condition: Optional[str]
    assembly: Optional[str]
    driverType: Optional[str]
    transmission: Optional[str]
    cylinder: Optional[int]
    engineSize: Optional[str]
    engineType: Optional[str]
    color: Optional[str]
    doors: Optional[int]
    seats: Optional[int]
    price: Optional[int]
    features: Optional[List[str]]

# Define the structure for the response
class ImageDetailsResponse(BaseModel):
    car_details: Optional[ImageCarDetails]
    error: Optional[str]

# Define the structure for the request
class CarDetailsRequest(BaseModel):
    front_image: str
    back_image: str
    right_side_image: str
    left_side_image: str
    interior_image: List[str]
    damage_part_image: Optional[List[str]]
    special_option_image: Optional[List[str]]

def expand_color_matches(user_colors: List[str], allowed_colors: List[str]) -> List[str]:
    matches = set()
    for base_color in user_colors:
        base_lower = base_color.lower()
        for allowed in allowed_colors:
            allowed_lower = allowed.lower()
            if base_lower in allowed_lower:
                matches.add(allowed)
    return list(matches)

@app.post("/prompt-search/", response_model=SearchCarDetailsResponse)
async def search_listing(car_request: SearchCarRequest):
    try:
        # Prepare the prompt for GPT-4 Vision
        search_prompt = f"""
            I will provide details about a car that I am looking for, and I need you to extract or infer all relevant information based on the provided query:
            
            - Make: (Car manufacturer, e.g., Toyota, Honda, etc.)
            - Model: (Specific model, e.g., Corolla, Model S, etc.)
            - Year From: (Earliest acceptable year based on user input)
            - Year To: (Latest acceptable year based on user input)
            - Mileage From: (Minimum acceptable odometer reading based on user input)
            - Mileage To: (Maximum acceptable odometer reading based on user input)
            - Body Type: (If mentioned or inferable from make and model, e.g., Sedan, SUV, Hatchback, etc.)
            - Condition: (New, Used, or condition details based on description)
            - Assembly: (Local or Imported)
            - Driver Type: (Left-hand drive or Right-hand drive)
            - Transmission: (Automatic, Manual, or specific details like 5-Speed Manual)
            - Engine Cylinder: (Number of cylinders, if available or inferable)
            - Engine Size: (If provided, e.g., 2.0L, or inferable based on model)
            - Engine Type: (Fuel type: Petrol, Diesel, Hybrid, Electric, etc.)
            - Registration Status: (Whether the car is registered, True or False)
            - Exterior Color: (Specific color if mentioned)
            - Number of Doors: (E.g., 2-door, 4-door)
            - Seats: (Number of seats if provided or inferable from make and model)
            - Price From: (Minimum acceptable price based on user input)
            - Price To: (Maximum acceptable price based on user input)
            - Country: ({', '.join(countries)} — follow the rule above)
            - City: (If mentioned or inferable from context)
            - Website: (Reference to where this car might be listed for sale)
            - Features: (Any special features like sunroof, navigation, leather seats, etc.)

            Please extract and infer as much information as possible from the user's input. Highlight any missing or unclear information in your response, and suggest possible answers where appropriate.
        """

        # Use OpenAI to extract car make, model, and year from the user's query
        completion = openai_client.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "system", "content": search_prompt},
                {"role": "user", "content": car_request.query},
            ],
            response_format=SearchCarDetailsResponse
        )

        # Process the OpenAI response
        message = completion.choices[0].message
        if message.parsed:
            base_color = message.parsed.car_details.color
            if base_color:
                if not isinstance(base_color, list):
                    base_color = [base_color]
                expanded_colors = expand_color_matches(base_color, color_str_list)
                expanded_colors = [get_id('color', c) for c in expanded_colors]
            else:
                expanded_colors = None
            # Parse the extracted car details from GPT-4 Vision response
            car_details = {
                'make': get_id('make', message.parsed.car_details.make),
                'model': get_id('model', message.parsed.car_details.model),
                'year_from': message.parsed.car_details.year_from or 0,
                'year_to': message.parsed.car_details.year_to or 0,
                'mileage_from': message.parsed.car_details.mileage_from or 0,
                'mileage_to': message.parsed.car_details.mileage_to or 0,
                'bodyType': get_id('bodyType', message.parsed.car_details.bodyType),
                'condition': get_id('condition', message.parsed.car_details.condition),
                'assembly': get_id('assembly', message.parsed.car_details.assembly),
                'driverType': get_id('driverType', message.parsed.car_details.driverType),
                'transmission': get_id('transmission', message.parsed.car_details.transmission),
                'cylinder': message.parsed.car_details.cylinder,
                'engineSize': message.parsed.car_details.engineSize,
                'engineType': get_id('engineType', message.parsed.car_details.engineType),
                'registrationStatus': message.parsed.car_details.registrationStatus,
                'color': get_id('color', base_color),
                'expandColors': expanded_colors,
                'doors': message.parsed.car_details.doors,
                'seats': message.parsed.car_details.seats,
                'price_from': message.parsed.car_details.price_from or 0,
                'price_to': message.parsed.car_details.price_to or 0,
                'country': message.parsed.car_details.country,
                'city': message.parsed.car_details.city,
                'website': get_id('website', message.parsed.car_details.website),
                'features': message.parsed.car_details.features
            }

            return SearchCarDetailsResponse(car_details=SearchCarDetails(**car_details), error=None)
        
        else:
            raise HTTPException(status_code=400, detail="Could not extract make, model, or year from the query.")
        
    except Exception as e:
        return HTTPException(car_details=None, error=f"Error: {str(e)}")

# # Helper function to save uploaded files temporarily
# async def save_image(image: UploadFile, filename: str) -> str:
#     file_path = f"/tmp/{filename}"
#     async with aiofiles.open(file_path, 'wb') as out_file:
#         while content := await image.read(1024):
#             await out_file.write(content)
#     return file_path

# Route to process uploaded images and extract car information
@app.post("/extract-car-details/", response_model=ImageDetailsResponse)
async def extract_car_details(car_detail_request: CarDetailsRequest):
    try:
        sub_interior_prompt = ''
        sub_damage_prompt = ''
        sub_special_prompt = ''

        sub_interior_prompt = f'- Interior ({len(car_detail_request.interior_image)} images)'
        if len(car_detail_request.special_option_image) > 0:
            sub_damage_prompt = f'- Special Option ({len(car_detail_request.special_option_image)} images)'
        if len(car_detail_request.damage_part_image) > 0:
            sub_special_prompt = f'- Damage part ({len(car_detail_request.damage_part_image)} images)'

        # Prepare the prompt for GPT-4 Vision
        vision_prompt = f"""
            I am providing images and details of a car for analysis. Your task is to extract key information and write a description that sounds natural and human-like, as if written by someone selling their car on a listing platform. Avoid overly polished or "AI-generated" language. Keep the tone simple, relatable, and conversational.
            In addition to creating the description, please extract and infer the following details from the images provided:

            - Make: (Manufacturer of the car, e.g., Toyota, Honda, etc.)
            - Model: (Specific car model, e.g., Corolla, Model S, etc.)
            - Year: (Year of manufacture, if visible or inferable)
            - Title: (A concise, attractive title suitable for a selling post)
            - Description: (Write a compelling description that highlights the car's unique selling points, features, and condition.)
            - Body Type: (Car type, e.g., Sedan, SUV, Compact, etc.)
            - Condition: (Assessed condition based on the images—e.g., excellent, good, used, etc.)
            - Assembly: (Whether the car is locally assembled or imported)
            - Driver Type: (Left-hand or right-hand drive)
            - Transmission: (Type of transmission—e.g., Automatic, Manual, 5-Speed Manual, etc.)
            - Engine Cylinder: (Number of cylinders, if visible or inferred from model)
            - Engine Size: (Engine capacity, e.g., 2.0L, if known or inferred)
            - Engine Type: (Fuel type, e.g., Petrol, Diesel, Hybrid, Electric, etc.)
            - Exterior Color: (The car's color, as visible in the images)
            - Number of Doors: (E.g., 2-door, 4-door, based on images or model)
            - Seats: (Number of seats, either visible or inferred from the car type/model)
            - Price: (A suggested selling price in USD based on the car's details and condition)
            - Features: (Any additional or special features—e.g., sunroof, navigation system, leather seats, etc.)

            The images are provided in the following sequence:
            - Front view
            - Back view
            - Right side view
            - Left side view
            {sub_interior_prompt}
            {sub_special_prompt}
            {sub_damage_prompt}

            Ensure the description is relatable and captures the car's condition and appeal naturally.
        """


        content = [
            {"type": "text", "text": str(vision_prompt)},
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
            }
        ]

        for url in car_detail_request.interior_image:
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": url,
                    "detail": "low"
                },
            })

        if car_detail_request.special_option_image:
            for url in car_detail_request.special_option_image:
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": url,
                        "detail": "low"
                    },
                })
        
        if car_detail_request.damage_part_image:
            for url in car_detail_request.damage_part_image:
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": url,
                        "detail": "low"
                    },
                })

        try:
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
                response_format=ImageDetailsResponse
            )


            # Extract the parsed information
            message = completion.choices[0].message

            if message.parsed:

                # Parse the extracted car details from GPT-4 Vision response
                car_details = {
                    # You would parse the details accordingly from the response here
                    'make': get_id('make', message.parsed.car_details.make),
                    'model': get_id('model', message.parsed.car_details.model),
                    'title': message.parsed.car_details.title,
                    'description': message.parsed.car_details.description,
                    'year': message.parsed.car_details.year,
                    'bodyType': get_id('bodyType', message.parsed.car_details.bodyType),
                    'condition': get_id('condition', message.parsed.car_details.condition),
                    'assembly': get_id('assembly', message.parsed.car_details.assembly),
                    'driverType': get_id('driverType', message.parsed.car_details.driverType),
                    'transmission': get_id('transmission', message.parsed.car_details.transmission),
                    'cylinder': message.parsed.car_details.cylinder,
                    'engineSize': message.parsed.car_details.engineSize,
                    'engineType': get_id('engineType', message.parsed.car_details.engineType),
                    'color': get_id('color', message.parsed.car_details.color),
                    'doors': message.parsed.car_details.doors,
                    'seats': message.parsed.car_details.seats,
                    'price': message.parsed.car_details.price,
                    'features': message.parsed.car_details.features
                }

                return ImageDetailsResponse(car_details=ImageCarDetails(**car_details), error=None)
                
        except Exception as e:
            return ImageDetailsResponse(car_details=None, error=f"Failed to extract car details: {str(e)}")
    
    except Exception as e:
        return HTTPException(car_details=None, error=f"Error: {str(e)}")