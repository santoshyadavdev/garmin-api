from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import os
import datetime
import logging
from garth.exc import GarthHTTPError
from garminconnect import (
    Garmin,
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
)

# Initialize the FastAPI app
app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables if defined
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")
TOKENSTORE = os.getenv("GARMINTOKENS") or "~/.garminconnect"

# Define the date range
today = datetime.date.today()
startdate = today - datetime.timedelta(days=7)

# Dependency to initialize the Garmin API
def get_garmin_api(email: str = EMAIL, password: str = PASSWORD):
    try:
        garmin = Garmin()
        garmin.login(TOKENSTORE)
    except (FileNotFoundError, GarthHTTPError, GarminConnectAuthenticationError):
        if not email or not password:
            raise HTTPException(status_code=401, detail="Email and password are required")
        try:
            garmin = Garmin(email=email, password=password, is_cn=False)
            garmin.login()
            garmin.garth.dump(TOKENSTORE)
        except (FileNotFoundError, GarthHTTPError, GarminConnectAuthenticationError, GarminConnectConnectionError) as err:
            logger.error(err)
            raise HTTPException(status_code=500, detail="Failed to authenticate with Garmin Connect")
    return garmin

@app.get("/get_full_name")
async def get_full_name(api: Garmin = Depends(get_garmin_api)):
    return {"full_name": api.get_full_name()}

@app.get("/get_unit_system")
async def get_unit_system(api: Garmin = Depends(get_garmin_api)):
    return {"unit_system": api.get_unit_system()}

@app.get("/get_activity_data")
async def get_activity_data(date: str = today.isoformat(), api: Garmin = Depends(get_garmin_api)):
    return {"activity_data": api.get_stats(date)}

@app.get("/get_body_composition")
async def get_body_composition(date: str = today.isoformat(), api: Garmin = Depends(get_garmin_api)):
    return {"body_composition": api.get_body_composition(date)}

@app.get("/get_steps_data")
async def get_steps_data(date: str = today.isoformat(), api: Garmin = Depends(get_garmin_api)):
    return {"steps_data": api.get_steps_data(date)}

@app.get("/get_heart_rate_data")
async def get_heart_rate_data(date: str = today.isoformat(), api: Garmin = Depends(get_garmin_api)):
    return {"heart_rate_data": api.get_heart_rates(date)}

@app.get("/get_training_readiness")
async def get_training_readiness(date: str = today.isoformat(), api: Garmin = Depends(get_garmin_api)):
    return {"training_readiness": api.get_training_readiness(date)}

@app.get("/get_activities")
async def get_activities(start: int = 0, limit: int = 100, api: Garmin = Depends(get_garmin_api)):
    return {"activities": api.get_activities(start, limit)}

@app.get("/get_last_activity")
async def get_last_activity(api: Garmin = Depends(get_garmin_api)):
    return {"last_activity": api.get_last_activity()}

# Add more routes here for other functionalities...

@app.get("/")
async def root():
    return {"message": "Garmin Connect API via FastAPI"}
