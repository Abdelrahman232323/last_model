import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from model.job_model import BERTJobRecommender
import os
import gc

logging.basicConfig(level=logging.INFO)

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
        data_path = os.path.join(os.path.dirname(__file__), 'data', 'Data_116.csv')
        if not os.path.exists(data_path):
            logging.error(f"Dataset not found at {data_path}")
            raise FileNotFoundError(f"Dataset not found at {data_path}")
        recommender = BERTJobRecommender(data_path)
        gc.collect()  # Force garbage collection after model loading
        logging.info("Model loaded successfully.")
    except Exception as e:
        logging.error(f"Failed to load model: {e}")
        raise

@app.get("/")
def root():
    return {"message": "BERT Job Recommender API is running!"}

@app.post("/recommend")
async def recommend_jobs(profile: UserProfile):
    try:
        global recommender
        if recommender is None:
            logging.error("Model not loaded")
            raise HTTPException(status_code=503, detail="Model not loaded")
        user_text = f"{profile.degree} in {profile.major}, GPA {profile.gpa}, " \
                    f"{profile.experience} years experience. Skills: {profile.skills}"
        recommendations = recommender.recommend(user_text, top_k=50)
        gc.collect()  # Clean up after processing
        return {"recommended_jobs": recommendations}
    except Exception as e:
        logging.error(f"[ERROR]: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# For Azure: Set the startup command to
# gunicorn -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")

logger = logging.getLogger("uvicorn.error")
logger.info("✅ App started successfully")