
import sqlite3
from database_func import connect_db
import google.generativeai as genai
import os
from chromadb.api.types import EmbeddingFunction

genai.configure(api_key=os.environ['GEMINI_API_KEY'])
def gemini_embedding(text):
    
    response = genai.embed_content(content=text, model="models/text-embedding-004")
    return response['embedding']




class GeminiEmbeddingFunction(EmbeddingFunction):
    def __call__(self, input):
        return [gemini_embedding(doc) for doc in input]

# Create embedding function instance



def fetch_job_descriptions(recruiter_code):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT jd.title, jd.description, jd.skills
        FROM job_descriptions jd
        JOIN recruiters r ON jd.recruiter_id = r.recruiter_id
        WHERE r.recruiter_code = ?
    """, (recruiter_code,))
    data = cursor.fetchall()
    conn.close()
    return [{"title": row[0], "description": row[1], "skills": row[2]} for row in data]

def fetch_resumes(recruiter_code, selected_title):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.student_code, s.name, rr.resume_text
        FROM recruiter_resumes rr
        JOIN students s ON rr.student_code = s.student_code
        WHERE rr.jd_title = ? AND rr.recruiter_code = ?
    """, (selected_title, recruiter_code))
    data = cursor.fetchall()
    conn.close()
    return [{"student_code": row[0], "name": row[1], "resume_text": row[2]} for row in data]


# def index_database_data(recruiter_code, chroma_collection):
#     # Fetch job descriptions
#     job_descriptions = fetch_job_descriptions(recruiter_code)
#     for jd in job_descriptions:
#         # jd_embedding = gemini_embedding(jd["description"] + "\nSkills: " + jd["skills"])
#         chroma_collection.add(
#             ids=[f"jd_{jd['title']}"],
#             documents=[jd["description"]],
#             # embeddings=[jd_embedding],
#             metadatas=[{
#                 "type": "job_description",
#                 "title": jd["title"],
#                 "description": jd["description"],
#                 "skills": jd["skills"]
#             }]
#         )

#     # Fetch resumes
#     for jd in job_descriptions:
#         resumes = fetch_resumes(recruiter_code, jd["title"])
#         for resume in resumes:
#             # resume_embedding = gemini_embedding(resume["resume_text"])
#             chroma_collection.add(
#                 ids=[f"resume_{resume['student_code']}"],
#                 documents=[resume["resume_text"]],
#                 # embeddings=[resume_embedding],
#                 metadatas=[{
#                     "type": "resume",
#                     "student_code": resume["student_code"],
#                     "name": resume["name"],
#                     "title": jd["title"],
#                     "resume_text": resume["resume_text"]
#                 }]
#             )
def index_database_data(recruiter_code, chroma_collection):
    # Fetch job descriptions
    job_descriptions = fetch_job_descriptions(recruiter_code)
    for jd in job_descriptions:
        jd_embedding = gemini_embedding(jd["description"] + "\nSkills: " + jd["skills"])
        chroma_collection.add(
            ids=[f"jd_{jd['title']}"],
            documents=[jd["description"]],
            # embeddings=[jd_embedding],
            metadatas=[{
                "type": "job_description",
                "title": jd["title"],
                "description": jd["description"],
                "skills": jd["skills"]
            }]
        )

    # Fetch resumes
    for jd in job_descriptions:
        resumes = fetch_resumes(recruiter_code, jd["title"])
        for resume in resumes:
            resume_embedding = gemini_embedding(resume["resume_text"])
            chroma_collection.add(
                ids=[f"resume_{resume['student_code']}"],
                documents=[resume["resume_text"]],
                # embeddings=[resume_embedding],
                metadatas=[{
                    "type": "resume",
                    "student_code": resume["student_code"],
                    "name": resume["name"],
                    "title": jd["title"],
                    "resume_text": resume["resume_text"]
                }]
            )