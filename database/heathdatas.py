from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
import mysql.connector
from database.connection import get_db_connection

router = APIRouter()


# Models
class HealthData(BaseModel):
    place: str
    age: int
    gender: str
    height_cm: float
    weight_kg: float
    heart_rate: int
    pre_existing_conditions: str

# Submit health data
@router.post("/health/{user_id}")
def submit_health_data(user_id: int, health_data: HealthData):
    db = get_db_connection()
    cursor = db.cursor()

    # Calculate BMI
    height_m = health_data.height_cm / 100
    bmi = round(health_data.weight_kg / (height_m ** 2), 2)

    try:
        cursor.execute(
            "INSERT INTO health_data (user_id, place, age, gender, height_cm, weight_kg, heart_rate, pre_existing_conditions, bmi) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (user_id, health_data.place, health_data.age, health_data.gender, health_data.height_cm, health_data.weight_kg, health_data.heart_rate, health_data.pre_existing_conditions, bmi)
        )
        db.commit()
        return {"message": "Health data submitted successfully", "bmi": bmi}
    except mysql.connector.Error as err:
        raise HTTPException(status_code=400, detail=str(err))
    finally:
        cursor.close()
        db.close()

# Fetch health data for a user
@router.get("/health/{user_id}")
def get_health_data(user_id: int):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM health_data WHERE user_id = %s", (user_id,))
        health_data = cursor.fetchone()
        if health_data:
            return health_data
        else:
            raise HTTPException(status_code=404, detail="Health data not found")
    except mysql.connector.Error as err:
        raise HTTPException(status_code=400, detail=str(err))
    finally:
        cursor.close()
        db.close()

# Update health data
@router.put("/health/{health_id}")
def update_health_data(health_id: int, health_data: HealthData):
    db = get_db_connection()
    cursor = db.cursor()

    # Calculate BMI
    height_m = health_data.height_cm / 100
    bmi = round(health_data.weight_kg / (height_m ** 2), 2)

    try:
        cursor.execute(
            "UPDATE health_data SET place = %s, age = %s, gender = %s, height_cm = %s, weight_kg = %s, heart_rate = %s, pre_existing_conditions = %s, bmi = %s "
            "WHERE id = %s",
            (health_data.place, health_data.age, health_data.gender, health_data.height_cm, health_data.weight_kg, health_data.heart_rate, health_data.pre_existing_conditions, bmi, health_id)
        )
        db.commit()
        return {"message": "Health data updated successfully", "bmi": bmi}
    except mysql.connector.Error as err:
        raise HTTPException(status_code=400, detail=str(err))
    finally:
        cursor.close()
        db.close()