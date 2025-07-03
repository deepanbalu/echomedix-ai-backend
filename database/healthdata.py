from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
import mysql.connector
from database.connection import get_db_connection

router = APIRouter()

class Placement(BaseModel):
    user_name: str
    college_name: str
    phone_number: str
    degree_name: str
    current_office_name: str
    place: str

# Models
class HealthData(BaseModel):
    place: str
    age: int
    gender: str
    height_cm: float
    weight_kg: float
    heart_rate: int
    pre_existing_conditions: str


# Submit placement details
@router.post("/placements/{user_id}")
def submit_placement(user_id: int, placement: Placement):
    db = get_db_connection()
    cursor = db.cursor()
    try:
        cursor.execute(
            "INSERT INTO placements (user_id, user_name, college_name, phone_number, degree_name, current_office_name, place) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (user_id, placement.user_name, placement.college_name, placement.phone_number, placement.degree_name, placement.current_office_name, placement.place)
        )
        db.commit()
        return {"message": "Placement details submitted successfully"}
    except mysql.connector.Error as err:
        raise HTTPException(status_code=400, detail=str(err))
    finally:
        cursor.close()
        db.close()

# Fetch placement details for a user
@router.get("/placements/{user_id}")
def get_placement(user_id: int):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM placements WHERE user_id = %s", (user_id,))
        placement_data = cursor.fetchone()
        if placement_data:
            return placement_data
        else:
            raise HTTPException(status_code=404, detail="Placement details not found")
    except mysql.connector.Error as err:
        raise HTTPException(status_code=400, detail=str(err))
    finally:
        cursor.close()
        db.close()

# Update placement details
@router.put("/placements/{placement_id}")
def update_placement(placement_id: int, placement: Placement):
    db = get_db_connection()
    cursor = db.cursor()
    try:
        cursor.execute(
            "UPDATE placements SET user_name = %s, college_name = %s, phone_number = %s, degree_name = %s, current_office_name = %s, place = %s WHERE id = %s",
            (placement.user_name, placement.college_name, placement.phone_number, placement.degree_name, placement.current_office_name, placement.place, placement_id)
        )
        db.commit()
        return {"message": "Placement details updated successfully"}
    except mysql.connector.Error as err:
        raise HTTPException(status_code=400, detail=str(err))
    finally:
        cursor.close()
        db.close()



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