from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from model.job_model import BERTJobRecommender
import os
import gc
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Job Recommender API", 
             description="A FastAPI-based job recommender system using BERT model",
             version="1.0.0")

recommender = None

class UserProfile(BaseModel):
    name: str
    degree: str
    major: str
    gpa: float
    experience: int
    skills: str

@app.on_event("startup")
async def load_model():
    global recommender
    try:
        data_path = "data_Set/Data.csv"
        if not os.path.exists(data_path):
            raise FileNotFoundError(f"Dataset not found at {data_path}")
        
        logger.info("Loading BERT model...")
        recommender = BERTJobRecommender(data_path)
        logger.info("Model loaded successfully")
        
        # Force garbage collection
        gc.collect()
    except Exception as e:
        logger.error(f"Failed to load model: {str(e)}")
        raise

@app.get("/")
def root():
    return {"message": "BERT Job Recommender API is running!"}

@app.post("/recommend")
async def recommend_jobs(profile: UserProfile):
    try:
        global recommender
        if recommender is None:
            raise HTTPException(status_code=503, detail="Model not loaded")
            
        user_text = f"{profile.degree} in {profile.major}, GPA {profile.gpa}, " \
                    f"{profile.experience} years experience. Skills: {profile.skills}"
        
        logger.info(f"Processing recommendation for user: {profile.name}")
        recommendations = recommender.recommend(user_text, top_k=50)
        
        # Clean up
        gc.collect()
        
        return {"recommended_jobs": recommendations}
    except Exception as e:
        logger.error(f"Error during recommendation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        gc.collect()