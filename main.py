from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from model.job_model import BERTJobRecommender
import os
import gc
import logging
import sys
from typing import Optional
import uvicorn
import psutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Initialize FastAPI with proper configuration
app = FastAPI(
    title="Job Recommender API",
    description="A FastAPI-based job recommender system using BERT model",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Global variables
recommender = None
MODEL_LOADED = False

class UserProfile(BaseModel):
    name: str
    degree: str
    major: str
    gpa: float
    experience: int
    skills: str

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global error handler caught: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please try again later."}
    )

@app.on_event("startup")
async def startup_event():
    global recommender, MODEL_LOADED
    try:
        logger.info("Starting application initialization...")
        data_path = os.path.join(os.path.dirname(__file__), "data", "Data_116.csv")
        
        if not os.path.exists(data_path):
            logger.error(f"Dataset not found at {data_path}")
            raise FileNotFoundError(f"Dataset not found at {data_path}")
            
        logger.info("Loading BERT model...")
        recommender = BERTJobRecommender(data_path)
        MODEL_LOADED = True
        logger.info("Model loaded successfully")
        
        # Force garbage collection
        gc.collect()
        
    except Exception as e:
        logger.error(f"Failed to load model: {str(e)}", exc_info=True)
        MODEL_LOADED = False
        raise

@app.get("/")
async def root():
    try:
        return {
            "status": "healthy",
            "message": "BERT Job Recommender API is running!",
            "model_loaded": MODEL_LOADED
        }
    except Exception as e:
        logger.error(f"Error in root endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    try:
        return {
            "status": "healthy",
            "model_loaded": MODEL_LOADED,
            "memory_usage": f"{psutil.Process().memory_info().rss / 1024 / 1024:.2f} MB"
        }
    except Exception as e:
        logger.error(f"Error in health check: {str(e)}", exc_info=True)
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@app.post("/recommend")
async def recommend_jobs(profile: UserProfile):
    try:
        global recommender
        if not MODEL_LOADED or recommender is None:
            logger.error("Model not loaded when recommendation requested")
            raise HTTPException(status_code=503, detail="Model not loaded. Please try again in a few moments.")
            
        logger.info(f"Processing recommendation request for user: {profile.name}")
        user_text = f"{profile.degree} in {profile.major}, GPA {profile.gpa}, " \
                    f"{profile.experience} years experience. Skills: {profile.skills}"
        
        recommendations = recommender.recommend(user_text, top_k=50)
        logger.info(f"Successfully generated recommendations for user: {profile.name}")
        
        # Force garbage collection
        gc.collect()
        
        return {"recommended_jobs": recommendations}
    except Exception as e:
        logger.error(f"Error in recommendation endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# Run the application
if __name__ == "__main__":
    # Get port from environment variable or default to 8000
    port = int(os.getenv("PORT", 8000))
    
    # Configure uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",  # Changed from 127.0.0.1 to 0.0.0.0 for Azure
        port=port,
        reload=False,  # Disabled reload in production
        log_level="info",
        workers=1  # Start with single worker
    )