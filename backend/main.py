# backend/main.py

import logging
from fastapi import FastAPI, Depends
from dotenv import load_dotenv
from contextlib import asynccontextmanager
import uvicorn
from backend.models.models import create_db_and_tables
from backend.routes import agents, appointments, patients, whatsapp

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Code to run on startup
    logger.info("Starting up HealthBridge AI...")
    logger.info("Attempting to create database and tables if they don't exist.")
    try:
        create_db_and_tables()
    except Exception as e:
        logger.error(f"Could not connect to the database or create tables: {e}")
        # Depending on the severity, you might want to prevent the app from starting
        # raise e 
    yield
    # Code to run on shutdown
    logger.info("Shutting down HealthBridge AI...")


# Initialize the FastAPI application
app = FastAPI(
    title="HealthBridge AI",
    description="A multi-agent healthcare system for patient communication and appointment management in Kenya.",
    version="1.0.0",
    lifespan=lifespan,
    contact={
        "name": "Project Lead",
        "email": "lead@healthbridge.ai",
    },
    license_info={
        "name": "MIT License",
    },
)

# --- Include API Routers ---
# Each router handles a specific domain of the application
app.include_router(agents.router)
app.include_router(appointments.router)
app.include_router(patients.router)
app.include_router(whatsapp.router)


# --- Root Endpoint ---
@app.get("/", tags=["Root"])
async def read_root():
    """
    Root endpoint providing basic information about the API.
    """
    return {
        "message": "🏥 HealthBridge AI - Multi-Agent Healthcare System",
        "status": "active",
        "version": "1.0.0",
        "documentation": "/docs"
    }

# To run the application:
# uvicorn backend.main:app --reload

if __name__ =="__main__" :
    print("Starting application...")
    print("Listening on http://localhost:8000")
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True, reload_dirs=["backend", "agents", "utils"])
    