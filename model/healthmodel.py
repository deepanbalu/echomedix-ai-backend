from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
import mysql.connector
import joblib
import numpy as np
import requests
from database.connection import get_db_connection
import google.generativeai as genai
import os

router = APIRouter()

# Get the current script directory
script_dir = os.path.dirname(os.path.abspath(__file__))

# Construct path to the model folder relative to the script directory
model_path = os.path.join(script_dir, '..', 'models', 'health_risk_prediction_model.pkl')
scaler_path = os.path.join(script_dir, '..', 'models', 'scaler.pkl')

# Load model and scaler
model = joblib.load(model_path)
scaler = joblib.load(scaler_path)

# Define mappings
gender_mapping = {"Female": 0, "Male": 1}
pre_existing_conditions_mapping = {
    "Normal": 0,
    "Respiratory Issues": 1,
    "Skin Conditions": 2,
    "Diabetes": 3,
    "Asthma": 4,
    "Hypertension": 5,
    "Cold & Cough": 6,
    "Heart Disease": 7,
    "Allergies": 8,
    "Fever": 9
}

# Function to fetch weather data
def fetch_weather_data(place, api_key):
    """Fetches AQI, temperature, and humidity for a given place."""
    geocode_url = f"http://api.openweathermap.org/data/2.5/weather?q={place}&appid={api_key}"
    aqi_url = f"https://api.openweathermap.org/data/2.5/air_pollution?lat={{lat}}&lon={{lon}}&appid={api_key}"

    try:
        # Fetch latitude and longitude
        geocode_response = requests.get(geocode_url)
        geocode_response.raise_for_status()
        geocode_data = geocode_response.json()
        lat = geocode_data['coord']['lat']
        lon = geocode_data['coord']['lon']

        # Fetch weather and AQI data
        weather_response = requests.get(geocode_url)
        weather_response.raise_for_status()
        weather_data = weather_response.json()

        aqi_response = requests.get(aqi_url.format(lat=lat, lon=lon))
        aqi_response.raise_for_status()
        aqi_data = aqi_response.json()

        # Extract relevant data
        aqi = aqi_data['list'][0]['main']['aqi']
        temperature = weather_data['main']['temp']
        humidity = weather_data['main']['humidity']
        pollution_level = aqi_data['list'][0]['components'].get('pm2_5', 0)

        return aqi, temperature, humidity, pollution_level

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Error fetching weather data: {e}")


# Initialize Gemini API
genai.configure(api_key="AIzaSyCPjQ-WTKQ5o705dvLjbFkryngXuF_06Oc")

def get_health_recommendation(health_data, weather_data, risk_level):
    """Get health recommendations using the Gemini API."""
    try:
        # Prepare the prompt
        prompt = f"""
        You are a professional health advisor. Provide **brief, easy-to-read, and actionable** health tips based on the user's profile. please don't say here are your personalized health recommendations:

        ### User Health Details:
        - **Age:** {health_data['age']}
        - **Gender:** {health_data['gender']}
        - **BMI:** {health_data['bmi']}
        - **Heart Rate:** {health_data['heart_rate']} bpm
        - **Pre-existing Conditions:** {health_data['pre_existing_conditions']}

        ### Environmental Conditions:
        - **Location:** {health_data['place']}
        - **Air Quality Index (AQI):** {weather_data['aqi']}
        - **Temperature:** {weather_data['temperature']}°C
        - **Humidity:** {weather_data['humidity']}%
        - **Pollution Level:** {weather_data['pollution_level']}

        ### Predicted Health Risk Level: **{risk_level}** 

        ### **Short & Focused Recommendations:**
        **Diet:** Eat more "fresh fruits", "lean protein", "whole grains" avoid "processed foods", "salty snacks", "fried foods"
        **Hydration:** Drink"2L", "2.5L", "3L" of water daily. Avoid sugary drinks.
        **Exercise:** "Walk daily", "Do light yoga", "Avoid outdoor workouts"
        **Precautions:** "Wear a mask (AQI high)", "Stay indoors during peak heat", "Monitor heart rate"
        **Doctor Advice:** "Check BP regularly", "Visit a doctor if symptoms worsen", "Emergency care if chest pain occurs"

        **Keep it short, clear, and easy to read! No unnecessary explanations.**
        Provide **personalized health recommendations** based on the user's health profile and environmental conditions. Please include any necessary precautions or actions to take.like drinking of water and what foods to do eat. and what foods to avoid. and what exercises to do. and what exercises to avoid. and what medications to take. and what medications to avoid.
        """


        # Call the Gemini API
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(prompt)
         # Transform the recommendations
        recommendations = response.text.strip()

        # Remove ** and replace with <strong> tags
        recommendations = recommendations.replace("**", "<strong>").replace("<strong>", "</strong>", 1)
        return recommendations

    except Exception as e:
        print("Error calling Gemini API:", str(e))
        return "Unable to fetch recommendations at the moment."

@router.post("/predict/{user_id}")
def predict_health_risk(user_id: int):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
        # Fetch user's health data
        cursor.execute("SELECT * FROM health_data WHERE user_id = %s", (user_id,))
        health_data = cursor.fetchone()
        if not health_data:
            raise HTTPException(status_code=404, detail="Health data not found")

        # Fetch weather data
        api_key = "ef1e161f88a398868c3033e43976bfa2"  # Replace with your OpenWeatherMap API key
        aqi, temperature, humidity, pollution_level = fetch_weather_data(health_data['place'], api_key)

        # Prepare input for the model
        input_data = np.array([
            health_data['age'],
            gender_mapping[health_data['gender']],
            health_data['bmi'],
            health_data['heart_rate'],
            pre_existing_conditions_mapping[health_data['pre_existing_conditions']],
            aqi,
            temperature,
            humidity,
            pollution_level
        ]).reshape(1, -1)

        # Scale the input data
        input_data_scaled = scaler.transform(input_data)

        # Make prediction
        prediction = model.predict(input_data_scaled)[0]
        risk_levels = {0: "Low", 1: "Medium", 2: "High"}
        risk_level = risk_levels[prediction]

        # Get recommendations from Gemini API
        weather_data = {
            "aqi": aqi,
            "temperature": temperature,
            "humidity": humidity,
            "pollution_level": pollution_level
        }
        recommendation = get_health_recommendation(health_data, weather_data, risk_level)

        return {
            "risk_level": risk_level,
            "recommendation": recommendation
        }

    except Exception as e:
        print("Error during prediction:", str(e))
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        db.close()
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
        # Fetch user's health data
        cursor.execute("SELECT * FROM health_data WHERE user_id = %s", (user_id,))
        health_data = cursor.fetchone()
        if not health_data:
            raise HTTPException(status_code=404, detail="Health data not found")

        print("Fetched health data:", health_data)  # Debugging log

        # Fetch weather data
        api_key = "ef1e161f88a398868c3033e43976bfa2"  # Replace with your OpenWeatherMap API key
        aqi, temperature, humidity, pollution_level = fetch_weather_data(health_data['place'], api_key)

        print("Fetched weather data:", {  # Debugging log
            "aqi": aqi,
            "temperature": temperature,
            "humidity": humidity,
            "pollution_level": pollution_level
        })

        # Prepare input for the model
        input_data = np.array([
            health_data['age'],
            gender_mapping[health_data['gender']],
            health_data['bmi'],
            health_data['heart_rate'],
            pre_existing_conditions_mapping[health_data['pre_existing_conditions']],
            aqi,
            temperature,
            humidity,
            pollution_level
        ]).reshape(1, -1)

        print("Input data for model:", input_data)  # Debugging log

        # Scale the input data
        input_data_scaled = scaler.transform(input_data)

        print("Scaled input data:", input_data_scaled)  # Debugging log

        # Make prediction
        prediction = model.predict(input_data_scaled)[0]
        risk_levels = {0: "Low", 1: "Medium", 2: "High"}
        risk_level = risk_levels[prediction]

        return {"risk_level": risk_level}

    except Exception as e:
        print("Error during prediction:", str(e))  # Debugging log
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        db.close()