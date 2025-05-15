from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from model.job_model import BERTJobRecommender
import os
import gc

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
        data_path = "data/wuzzuf_02_4_part3.csv"
        if not os.path.exists(data_path):
            raise FileNotFoundError(f"Dataset not found at {data_path}")
        recommender = BERTJobRecommender(data_path)
        gc.collect()  # Force garbage collection after model loading
    except Exception as e:
        print(f"[ERROR] Failed to load model: {e}")
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
        
        recommendations = recommender.recommend(user_text, top_k=10)
        gc.collect()  # Clean up after processing
        return {"recommended_jobs": recommendations}
    except Exception as e:
        print(f"[ERROR]: {e}")
        raise HTTPException(status_code=500, detail=str(e))
