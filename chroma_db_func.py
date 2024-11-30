
import sqlite3
from database_func import connect_db
import google.generativeai as genai
import os
from chromadb.api.types import EmbeddingFunction
import streamlit as st

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



def fetch_student_resume(student_code): #single student
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT rr.resume_text
        FROM recruiter_resumes rr
        JOIN students s ON rr.student_code = s.student_code
        WHERE rr.student_code = ?
    """, (student_code,))
    data = cursor.fetchone()
    conn.close()
    return data[0]


def index_database_data_for_student(recruiter_code, student_code, chroma_collection):
    # Fetch all job descriptions for the given recruiter
    job_descriptions = fetch_job_descriptions(recruiter_code)
    
    # Add job descriptions to the Chroma collection
    for jd in job_descriptions:
        chroma_collection.add(
            ids=[f"jd_{jd['title']}"],
            documents=[jd["description"]],
        )
    
    # Fetch the single student's resume
    resume_text = fetch_student_resume(student_code)
    
    if resume_text:
        chroma_collection.add(
            ids=[f"resume_{student_code}"],
            documents=[resume_text],
        )
    else:
        st.write(f"No resume found for student_code: {student_code}")
    
