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
website_collection = db['website']

make_list = list(make_collection.find({}, { 'name': 1 }))
model_list = list(model_collection.find({}, { 'name': 1 }))
bodyType_list = list(bodyType_collection.find({}, { 'name': 1 }))
condition_list = list(condition_collection.find({}, { 'name': 1 }))
assembly_list = list(assembly_collection.find({}, { 'name': 1 }))
driverType_list = list(driverType_collection.find({}, { 'name': 1 }))
transmission_list = list(transmission_collection.find({}, { 'name': 1 }))
engineType_list = list(engineType_collection.find({}, { 'name': 1 }))
website_list = list(website_collection.find({}, { 'name': 1 }))

# OpenAI API key
with open('credential.json') as json_file:
    cred_data = json.load(json_file)
api_key = cred_data['open_ai_key']
openai_client = OpenAI(api_key=api_key)

def get_id(col_name, field_value):
    result = None
    global make_list
    global model_list
    global bodyType_list
    global condition_list
    global assembly_list
    global driverType_list
    global transmission_list
    global engineType_list
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
        elif col_name == 'website':
            col_list = website_list

        for doc in col_list:
            if doc.get('name') == field_value:
                result = doc
                break
        
        if result:
            return str(result.get('_id'))
        else:
            return None

    else:
        return None

# Define the structure to hold the car's extracted information
class SearchCarDetails(BaseModel):
    make: Optional[str]
    model: Optional[str]
    year: Optional[int]
    mileage: Optional[int]
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
    doors: Optional[int]
    seats: Optional[int]
    price: Optional[int]
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

# Define the structure for the request
class CarDetailsRequest(BaseModel):
    front_image: str
    back_image: str
    right_side_image: str
    left_side_image: str
    interior_image: str
    damage_part_image: Optional[str]
    special_option_image: Optional[str]

@app.post("/prompt-search/", response_model=SearchCarDetailsResponse)
async def search_listing(car_request: SearchCarRequest):
    # Prepare the prompt for GPT-4 Vision
    search_prompt = f"""
        I will provide details about a car that I am looking for, and I need you to extract or infer all relevant information based on the provided query:
        
        - Make: (Car manufacturer, e.g., Toyota, Honda, etc.)
        - Model: (Specific model, e.g., Corolla, Model S, etc.)
        - Year: (Year of manufacture or range)
        - Mileage: (Odometer reading or approximate estimation)
        - Body Type: (If mentioned or inferable from make and model i.e. Sedan, SUV, Hatchback, etc.)
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
        - Price: (Suggested selling price in USD or range based on details)
        - Country: (If mentioned or inferable from context)
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
        # Parse the extracted car details from GPT-4 Vision response
        car_details = {
            'make': get_id('make', message.parsed.car_details.make),
            'model': get_id('model', message.parsed.car_details.model),
            'year': message.parsed.car_details.year,
            'mileage': message.parsed.car_details.mileage,
            'bodyType': get_id('bodyType', message.parsed.car_details.bodyType),
            'condition': get_id('condition', message.parsed.car_details.condition),
            'assembly': get_id('assembly', message.parsed.car_details.assembly),
            'driverType': get_id('driverType', message.parsed.car_details.driverType),
            'transmission': get_id('transmission', message.parsed.car_details.transmission),
            'cylinder': message.parsed.car_details.cylinder,
            'engineSize': message.parsed.car_details.engineSize,
            'engineType': get_id('engineType', message.parsed.car_details.engineType),
            'registrationStatus': message.parsed.car_details.registrationStatus,
            'color': message.parsed.car_details.color,
            'doors': message.parsed.car_details.doors,
            'seats': message.parsed.car_details.seats,
            'price': message.parsed.car_details.price,
            'country': message.parsed.car_details.country,
            'city': message.parsed.car_details.city,
            'website': get_id('website', message.parsed.car_details.website),
            'features': message.parsed.car_details.features
        }

        return SearchCarDetailsResponse(car_details=SearchCarDetails(**car_details), error=None)
    
    else:
        raise HTTPException(status_code=400, detail="Could not extract make, model, or year from the query.")

# Helper function to save uploaded files temporarily
async def save_image(image: UploadFile, filename: str) -> str:
    file_path = f"/tmp/{filename}"
    async with aiofiles.open(file_path, 'wb') as out_file:
        while content := await image.read(1024):
            await out_file.write(content)
    return file_path

# # Route to process uploaded images and extract car information
# @app.post("/extract-car-details/", response_model=CarDetailsResponse)
# async def extract_car_details(car_detail_request: CarDetailsRequest):
#     # Prepare the prompt for GPT-4 Vision
#     vision_prompt = f"""
#     I have provided images of a car. Please analyze these images and extract all relevant information based on the details I am seeking below. Be as thorough as possible and infer details from the images wherever applicable:
#     - Make: (Car manufacturer)
#     - Model: (Car model)
#     - Year: (Year of manufacture)
#     - VIN: (Vehicle Identification Number, if visible)
#     - Car type: (e.g., sedan, SUV, etc.)
#     - Mileage: (Odometer reading or estimation)
#     - Description: (A brief summary or description for a selling post)
#     - Condition: (Analyzed condition based on the images)
#     - Fuel type: (e.g., gasoline, diesel, electric)
#     - Number of cylinders: (Engine configuration)
#     - Engine size: (If visible or inferable)
#     - Registration status: (Visible details about registration)
#     - Color: (Main exterior color)
#     - Number of doors: (e.g., 2, 4)
#     - Price: (Suggested selling price in USD based on car's condition and details)
#     - Features: (Notable features such as sunroof, navigation system, leather seats, etc.)

#     The images you will get in following sequence:
#     - Front view:
#     - Back view:
#     - Right side view:
#     - Left side view:
#     - Interior:
#     - Damage part (optional):
#     - Special option part (optional):
#     """

#     content = [
#         {"type": "text", "text": vision_prompt},
#         {
#             "type": "image_url",
#             "image_url": {
#                 "url": car_detail_request.front_image,
#                 "detail": "low"
#             },
#         },
#         {
#             "type": "image_url",
#             "image_url": {
#                 "url": car_detail_request.back_image,
#                 "detail": "low"
#             },
#         },
#         {
#             "type": "image_url",
#             "image_url": {
#                 "url": car_detail_request.right_side_image,
#                 "detail": "low"
#             },
#         },
#         {
#             "type": "image_url",
#             "image_url": {
#                 "url": car_detail_request.left_side_image,
#                 "detail": "low"
#             },
#         },
#         {
#             "type": "image_url",
#             "image_url": {
#                 "url": car_detail_request.interior_image,
#                 "detail": "low"
#             },
#         }
#     ]

#     if car_detail_request.damage_part_image:
#         content.append({
#             "type": "image_url",
#             "image_url": {
#                 "url": car_detail_request.damage_part_image,
#                 "detail": "low"
#             },
#         })
#     if car_detail_request.special_option_image:
#         content.append({
#             "type": "image_url",
#             "image_url": {
#                 "url": car_detail_request.special_option_image,
#                 "detail": "low"
#             },
#         })

#     try:
#         # Use GPT-4 Vision to analyze the images and extract information
#         completion = openai_client.beta.chat.completions.parse(
#             model="gpt-4o-2024-08-06",
#             messages=[
#                 {
#                     "role": "system",
#                     "content": "You are an assistant that helps extract car information from images."
#                 },
#                 {
#                     "role": "user",
#                     "content": content
#                 }
#             ],
#             response_format=CarDetailsResponse
#         )


#         # Extract the parsed information
#         message = completion.choices[0].message

#         if message.parsed:

#             # Parse the extracted car details from GPT-4 Vision response
#             car_details = {
#                 # You would parse the details accordingly from the response here
#                 "make": message.parsed.car_details.make,
#                 "model": message.parsed.car_details.model,
#                 "year": message.parsed.car_details.year,
#                 "vin": message.parsed.car_details.vin,
#                 "type": message.parsed.car_details.type,
#                 "mileage": message.parsed.car_details.mileage,
#                 "description": message.parsed.car_details.description,
#                 "condition": message.parsed.car_details.condition,
#                 "fuel_type": message.parsed.car_details.fuel_type,
#                 "cylinder": message.parsed.car_details.cylinder,
#                 "engine_size": message.parsed.car_details.engine_size,
#                 "registration_status": message.parsed.car_details.registration_status,
#                 "color": message.parsed.car_details.color,
#                 "doors": message.parsed.car_details.doors,
#                 "price": message.parsed.car_details.price,
#                 "features": message.parsed.car_details.features
#             }

#             return CarDetailsResponse(car_details=CarDetails(**car_details), error=None)
            
#     except Exception as e:
#         return CarDetailsResponse(car_details=None, error=f"Failed to extract car details: {str(e)}")
