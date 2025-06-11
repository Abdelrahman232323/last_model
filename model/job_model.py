import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import re
from fuzzywuzzy import fuzz  # pip install fuzzywuzzy
import gc

class BERTJobRecommender:
    def __init__(self, data_path):
        # Load data with only necessary columns
        self.df = pd.read_csv(data_path, encoding="utf-8", 
                            usecols=['Job_Title', 'Company_Name', 'Skills', 'Job_Description', 
                                   'Job_Link', 'Experience_Level', 'Work_Type', 'Job_Type', 
                                   'Location', 'Date_Post', 'Image_Link'])
        self.df = self.df.dropna(subset=['Job_Title', 'Company_Name', 'Skills', 'Job_Description', 'Job_Link'])
        self.df = self.df.reset_index(drop=True)

        # Use smaller model for faster loading
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Process embeddings in smaller batches
        batch_size = 50  # Smaller batch size
        self.job_skills_embeddings = []
        
        print("📦 Encoding job skills...")
        for i in range(0, len(self.df), batch_size):
            batch = self.df['Skills'].iloc[i:i+batch_size]
            batch_texts = ['Skills: ' + ', '.join(self.preprocess_skills(s)) for s in batch]
            batch_embeddings = self.model.encode(batch_texts, show_progress_bar=False)
            self.job_skills_embeddings.extend(batch_embeddings)
            gc.collect()  # Clean up after each batch
            
        self.job_skills_embeddings = np.array(self.job_skills_embeddings)
        print("✅ Encoding complete!")

    def preprocess_skills(self, skills):
        if not isinstance(skills, str):
            return []
        skills = re.sub(r'[;]', ',', skills)
        return [skill.strip().lower() for skill in skills.split(',') if skill.strip()]

    def keyword_similarity_fuzzy(self, user_skills, job_skills):
        return fuzz.token_set_ratio(
            ' '.join(self.preprocess_skills(user_skills)), 
            ' '.join(self.preprocess_skills(job_skills))
        ) / 100.0

    def safe_float(self, value, default=0.0):
        try:
            if pd.isna(value) or np.isnan(value):
                return default
            return float(value)
        except:
            return default

    def recommend(self, user_text, top_k=10):
        try:
            skills = user_text.split("Skills:")[-1].strip()
            user_skills_processed = self.preprocess_skills(skills)
            formatted_user_text = 'Skills: ' + ', '.join(user_skills_processed)
            
            # Get user embedding
            user_embedding = self.model.encode([formatted_user_text])[0]

            # Calculate similarities
            semantic_similarities = cosine_similarity([user_embedding], self.job_skills_embeddings).flatten()
            keyword_similarities = self.df['Skills'].apply(lambda x: self.keyword_similarity_fuzzy(skills, x)).values

            # Handle NaN values
            semantic_similarities = np.nan_to_num(semantic_similarities, nan=0.0)
            keyword_similarities = np.nan_to_num(keyword_similarities, nan=0.0)

            combined_similarities = 0.5 * keyword_similarities + 0.5 * semantic_similarities

            self.df['semantic_similarity'] = semantic_similarities
            self.df['keyword_similarity'] = keyword_similarities
            self.df['combined_similarity'] = combined_similarities

            df_filtered = self.df[self.df['combined_similarity'] > 0.3]
            top_matches = df_filtered.sort_values(by='combined_similarity', ascending=False).head(top_k)

            results = []
            for idx, row in top_matches.iterrows():
                # Safely convert scores to float and handle NaN
                combined_score = self.safe_float(row['combined_similarity'])
                semantic_score = self.safe_float(row['semantic_similarity'])
                keyword_score = self.safe_float(row['keyword_similarity'])

                # Helper function to safely get string values
                def safe_get(value, default=''):
                    if pd.isna(value) or value is None:
                        return default
                    return str(value)

                result = {
                    "job_title": safe_get(row['Job_Title']),
                    "company": safe_get(row['Company_Name']),
                    "skills_required": safe_get(row['Skills']),
                    "combined_match_score": f"{round(combined_score * 100, 2)}%",
                    "semantic_score": f"{round(semantic_score * 100, 2)}%",
                    "keyword_score": f"{round(keyword_score * 100, 2)}%",
                    "job_link": safe_get(row['Job_Link']),
                    "job_description": safe_get(row.get('Job_Description'), ''),
                    "experience": safe_get(row.get('Experience_Level'), ''),
                    "work_type": safe_get(row.get('Work_Type'), ''),
                    "job_type": safe_get(row.get('Job_Type'), ''),
                    "location": safe_get(row.get('Location'), ''),
                    "date_posted": safe_get(row.get('Date_Post'), ''),
                    "image_link": safe_get(row.get('Image_Link'), '')
                }
                results.append(result)

            return results
            
        except Exception as e:
            print(f"Error in recommendation: {str(e)}")
            return []
        finally:
            gc.collect()  # Clean up after processing
