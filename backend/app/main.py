import os
from io import BytesIO
import logging
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from firebase_admin import auth, firestore, storage
from langchain_ollama.llms import OllamaLLM
from langchain_core.output_parsers import StrOutputParser
from app.firebase_admin import db  # Import the initialized Firestore client
from langchain.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
import google.generativeai as genai
from PIL import Image
from typing import List
import uuid


# Initialize logging
logger = logging.getLogger(__name__)

# Gemini API key
GOOGLE_API_KEY = "AIzaSyCzLk-nONdcr6Wd4_DPFpNsOfFNLhvY4BU"  
os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY


genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

#Pydantic Models

class QueryRequest(BaseModel):
    question: str


class TextInput(BaseModel):
    text: str

class Signup(BaseModel):
    name: str
    email: str
    password: str

class Login(BaseModel):
    email: str
    password: str

app = FastAPI()

# CORS Middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://192.168.29.75:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


#Route Handlers Defined

@app.get("/")
async def read_root():
    return {"message": "Welcome to the Travisco App!"}

@app.post("/signup")
async def post_signup(signup: Signup):
    try:
        user = auth.create_user(
            email=signup.email,
            password=signup.password,
            display_name=signup.name
        )
    
        db.collection('users').document(user.uid).set({
            'name': signup.name,
            'email': signup.email
        })
        return {"message": "Signup successful! Please check your email for verification."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/login")
async def post_login(login: Login):
    try:
        user = auth.get_user_by_email(login.email)
        return {"message": "Login successful!"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

#Monument Finder API
def get_gemini_response(input_prompt, image_or_text):
    try:
        # Send the image or text prompt to the model
        response = model.generate_content([input_prompt, image_or_text])

        # Expected response in the format:
        # "Monument Name: <name>\nDescription: <description>"
        response_text = response.text
        name = ""
        description = ""

        # Split response into lines and extract the relevant parts
        for line in response_text.split("\n"):
            if line.startswith("Monument Name:"):
                name = line.replace("Monument Name:", "").strip()
            elif line.startswith("Description:"):
                description = line.replace("Description:", "").strip()

        return {"monument_name": name, "description": description}
    except Exception as e:
        logging.error(f"Error generating response from Gemini: {str(e)}")
        raise HTTPException(status_code=500, detail="Error generating response from Gemini.")

def input_image_setup(image_file):
    try:
        image = Image.open(BytesIO(image_file))
        return image
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing image: {str(e)}")

input_prompt = input_prompt = """
You are an expert virtual tour guide. When shown an image of a monument, your task is to:
1. Recognize the monument from the image.
2. Return the name of the monument in the format: "Monument Name: <name>".
3. Provide a detailed description of the monument after the name in the format: "Description: <detailed description>".
Make sure to return the name and description in separate lines.
"""

#Main Route
@app.post("/find")
async def find_monument(file: UploadFile = File(None), text: str = Form(None)):
    try:
        if file:
            # Read the uploaded image file
            image_data = await file.read()  # Read the image data
            image = input_image_setup(image_data)  # Process the image using the input_image_setup function

            # Get the structured response (name and description)
            response_data = get_gemini_response(input_prompt, image)  # Pass the image directly

        elif text:
            # Get the structured response for the text input
            response_data = get_gemini_response(input_prompt, text)  # Pass the text directly

        else:
            raise HTTPException(status_code=400, detail="No valid input provided. Please provide either an image or text.")

        # Return the response data, which contains the name and description
        return JSONResponse(content=response_data)
    except Exception as e:
        logging.error(f"Error processing input: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
#Community Monument Wise

@app.get("/community/{monument_name}")
async def get_community(monument_name: str):
    try:
        if not monument_name:
            return {"message": "Monument name is required."}

        posts_ref = db.collection(monument_name)
        posts = posts_ref.stream()
        community_posts = []

        for post in posts:
            post_data = post.to_dict()
            post_data['id'] = post.id
            logging.info(f"Fetched post data: {post_data}")  # Log each post's data
            community_posts.append(post_data)

        if not community_posts:
            return {"message": "No posts available for this monument."}

        return {"posts": community_posts, "count": len(community_posts)}

    except Exception as e:
        logging.error(f"Error fetching community posts: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch community posts")

    
    except Exception as e:
        logging.error(f"Error fetching community posts: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch community posts")


#Community Post Creation

@app.post("/community/post")
async def post_community(
    Username: str = Form(...),
    Monument_name: str = Form(...),
    Description: str = Form(...),
    Review: str = Form(...),
    images: List[UploadFile] = File([]),  # Accept multiple images
    videos: List[UploadFile] = File([]),  # Accept multiple videos
    gifs: List[UploadFile] = File([])  # Accept multiple GIFs
):
    try:
        # Reference to your storage bucket
        bucket = storage.bucket("travisco-ca6c3.appspot.com")
        media_urls = {
            'image_urls': [],
            'video_urls': [],
            'gif_urls': []
        }

        # Upload all images
        for image in images:
            if image:
                image_url = await upload_file_to_storage(bucket, image, "images")
                media_urls['image_urls'].append(image_url)
                logging.info(f"Uploaded image URL: {image_url}")

        # Upload all videos
        for video in videos:
            if video:
                video_url = await upload_file_to_storage(bucket, video, "videos")
                media_urls['video_urls'].append(video_url)
                logging.info(f"Uploaded video URL: {video_url}")

        # Upload all GIFs
        for gif in gifs:
            if gif:
                gif_url = await upload_file_to_storage(bucket, gif, "gifs")
                media_urls['gif_urls'].append(gif_url)
                logging.info(f"Uploaded GIF URL: {gif_url}")

        # Prepare post data
        post_data = {
            'Username': Username,
            'Monument_name': Monument_name,
            'Description': Description,
            'Review': Review,
            'media_urls': media_urls
        }

        # Create a new document in the collection corresponding to the monument
        doc_ref = db.collection(Monument_name).document()  # Firestore collection based on monument name
        doc_ref.set(post_data)  # Save post data to Firestore
        logging.info(f"Post created: {post_data}")

        return {
            'message': 'Community post created successfully!',
            'post_id': doc_ref.id,  # Return the newly created document ID
            'post_data': post_data
        }

    except Exception as e:
        logging.error(f"Error creating community post: {e}")
        raise HTTPException(status_code=500, detail="Failed to create community post")


# Helper function to upload files to Google Cloud Storage
async def upload_file_to_storage(bucket, file: UploadFile, folder: str):
    try:
        # Generate a unique file name using UUID
        file_extension = file.filename.split('.')[-1]
        blob = bucket.blob(f"{folder}/{uuid.uuid4()}.{file_extension}")

        # Upload the file to the bucket
        blob.upload_from_file(file.file, content_type=file.content_type)
        blob.make_public()  # Make the file publicly accessible
        logging.info(f"File uploaded to: {blob.public_url}")

        return blob.public_url  # Return the public URL of the file

    except Exception as e:
        logging.error(f"Error uploading file to storage: {e}")
        raise HTTPException(status_code=500, detail="File upload failed")
    

#All Community Posts

@app.get("/community")
async def get_all_community_posts():
    try:
        # Fetch all community posts from all collections
        collections = db.collections()
        all_posts = []

        for collection in collections:
            posts = collection.stream()
            for post in posts:
                post_data = post.to_dict()
                post_data['id'] = post.id
                post_data['monument_name'] = collection.id  # Include monument name
                all_posts.append(post_data)

        if not all_posts:
            return {"message": "No community posts available."}

        return {"posts": all_posts, "count": len(all_posts)}

    except Exception as e:
        logging.error(f"Error fetching all community posts: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch community posts")
