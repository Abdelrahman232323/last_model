# bert_model.py
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import re
from fuzzywuzzy import fuzz

class BERTJobRecommender:
    def __init__(self, data_path: str):
        self.df = pd.read_csv(data_path, encoding="utf-8")
        self.df = self.df.dropna(subset=['Job_Title', 'Company_Name', 'Skills', 'Job_Description', 'Job_Link'])
        self.df = self.df.reset_index(drop=True)
        
        # Initialize the model
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Preprocess and encode job skills
        print("📦 Encoding job skills...")
        job_texts = ['Skills: ' + ', '.join(self.preprocess_skills(s)) for s in self.df['Skills']]
        self.job_skills_embeddings = self.model.encode(job_texts, show_progress_bar=True)

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

    def recommend(self, user_input: str, top_k: int = 10):
        # Process user input
        user_skills_processed = self.preprocess_skills(user_input)
        user_text = 'Skills: ' + ', '.join(user_skills_processed)
        user_embedding = self.model.encode([user_text])[0]

        # Calculate similarities
        semantic_similarities = cosine_similarity([user_embedding], self.job_skills_embeddings).flatten()
        keyword_similarities = self.df['Skills'].apply(lambda x: self.keyword_similarity_fuzzy(user_input, x)).values
        
        # Combine similarities with weights
        combined_similarities = 0.5 * keyword_similarities + 0.5 * semantic_similarities

        # Add similarity scores to dataframe
        self.df['semantic_similarity'] = semantic_similarities
        self.df['keyword_similarity'] = keyword_similarities
        self.df['combined_similarity'] = combined_similarities

        # Filter and sort results
        df_filtered = self.df[self.df['combined_similarity'] > 0.3]
        top_matches = df_filtered.sort_values(by='combined_similarity', ascending=False).head(top_k)

        # Format results
        results = top_matches[['Job_Title', 'Company_Name', 'Skills', 'Job_Link', 
                             'combined_similarity', 'semantic_similarity', 'keyword_similarity']].rename(
            columns={'Job_Link': 'apply_link'}
        )

        # Convert similarity scores to float
        for col in ['combined_similarity', 'semantic_similarity', 'keyword_similarity']:
            results[col] = results[col].astype(float)

        return results.to_dict(orient='records')

        