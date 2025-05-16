import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import re
from fuzzywuzzy import fuzz  # pip install fuzzywuzzy

class BERTJobRecommender:
    def __init__(self, data_path):
        self.df = pd.read_csv(data_path, encoding="utf-8")
        self.df = self.df.dropna(subset=['Job_Title', 'Company_Name', 'Skills', 'Job_Description', 'Job_Link'])
        self.df = self.df.reset_index(drop=True)

        self.model = SentenceTransformer('all-MiniLM-L6-v2')

        print("📦 Encoding job skills...")
        self.job_texts = ['Skills: ' + ', '.join(self.preprocess_skills(s)) for s in self.df['Skills']]
        self.job_skills_embeddings = self.model.encode(self.job_texts, show_progress_bar=True)

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

    def recommend(self, user_text, top_k=10):
        name = "API User"
        skills = user_text.split("Skills:")[-1].strip()
        user_skills_processed = self.preprocess_skills(skills)
        formatted_user_text = 'Skills: ' + ', '.join(user_skills_processed)
        user_embedding = self.model.encode([formatted_user_text])[0]

        semantic_similarities = cosine_similarity([user_embedding], self.job_skills_embeddings).flatten()
        keyword_similarities = self.df['Skills'].apply(lambda x: self.keyword_similarity_fuzzy(skills, x)).values

        combined_similarities = 0.5 * keyword_similarities + 0.5 * semantic_similarities

        self.df['semantic_similarity'] = semantic_similarities
        self.df['keyword_similarity'] = keyword_similarities
        self.df['combined_similarity'] = combined_similarities

        df_filtered = self.df[self.df['combined_similarity'] > 0.3]
        top_matches = df_filtered.sort_values(by='combined_similarity', ascending=False).head(top_k)

        results = []
        for idx, row in top_matches.iterrows():
            score = round(row['combined_similarity'] * 100, 2)
            result = {
                "job_title": row['Job_Title'],
                "company": row['Company_Name'],
                "skills_required": row['Skills'],
                "combined_match_score": f"{score}%",
                "semantic_score": f"{round(row['semantic_similarity'] * 100, 2)}%",
                "keyword_score": f"{round(row['keyword_similarity'] * 100, 2)}%",
                "job_link": row['Job_Link']
            }
            results.append(result)
        return results
