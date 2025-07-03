from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
import mysql.connector
from database.connection import get_db_connection


router = APIRouter()

# Models
class User(BaseModel):
    username: str
    password: str


# Register a new user
@router.post("/register")
def register(user: User):
    db = get_db_connection()
    cursor = db.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (user.username, user.password))
        db.commit()
        return {"message": "User registered successfully"}
    except mysql.connector.Error as err:
        raise HTTPException(status_code=400, detail=str(err))
    finally:
        cursor.close()
        db.close()

# Login (dummy implementation for simplicity)
@router.post("/login")
def login(user: User):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (user.username, user.password))
    user_data = cursor.fetchone()
    if user_data:
        return {"message": "Login successful", "user_id": user_data["id"]}
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")