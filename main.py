from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel
import mysql.connector
from fastapi.middleware.cors import CORSMiddleware
from database.auth import router as auth_router
from database.healthdata import router as healthdata_router
from model.healthmodel import router as healthmodel_router
from model.analyze import router as analyze_router
from database.connection import get_db_connection

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://echomedixsai.web.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    )


app.include_router(auth_router)
app.include_router(healthdata_router)
app.include_router(healthmodel_router)
app.include_router(analyze_router)


# Run the FastAPI app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)