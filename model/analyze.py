from fastapi import APIRouter
from fastapi import File, UploadFile, HTTPException
import pytesseract
from PIL import Image
import google.generativeai as genai
import os

# Create a router object to define routes
router = APIRouter()

# Configure Gemini API
genai.configure(api_key="AIzaSyDZF1WbX6FP39HtY_JnzNXWXoI3_B2iom0")

# Text extraction function using pytesseract
def extract_text_from_image(image_path):
    try:
        # Open the image using PIL
        img = Image.open(image_path)
        # Extract text using pytesseract
        text = pytesseract.image_to_string(img)
        return text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting text: {str(e)}")

# Generate recommendations using Gemini API
def generate_recommendations(text):
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        prompt = f"""
        The following text is extracted from a medical report. Provide detailed health recommendations based on the content:

        {text}

        Please provide actionable and personalized recommendations.
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating recommendations: {str(e)}")

# API endpoint for uploading medical report image
@router.post("/upload-report")
async def upload_report(file: UploadFile = File(...)):
    try:
        # Save the uploaded file temporarily
        file_path = f"temp_{file.filename}"
        with open(file_path, "wb") as buffer:
            buffer.write(file.file.read())

        # Extract text from the image
        extracted_text = extract_text_from_image(file_path)

        # Generate recommendations using Gemini API
        recommendations = generate_recommendations(extracted_text)

        # Clean up the temporary file
        os.remove(file_path)

        return {
            "extracted_text": extracted_text,
            "recommendations": recommendations,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))