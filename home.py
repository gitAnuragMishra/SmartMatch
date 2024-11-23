import streamlit as st
import fitz
from io import BytesIO
import pytesseract
from PIL import Image
import sqlite3
import os
import shutil
import re
import json

with open("extractor_library.json", "r") as file:
    skills_data = json.load(file)

skills_list = skills_data["skills_list"]

import google.generativeai as genai
genai.configure(api_key=os.environ['GEMINI_API_KEY'])

from database_func import add_recruiter, validate_recruiter, recruiter_exists, get_job_descriptions, save_job_description, delete_all_job_descriptions, student_exists, add_student, validate_student, connect_db, extract_skills#, delete_job_description  # Import functions from the database module

# Set page configuration
st.set_page_config(page_title="SmartMatch", page_icon=":briefcase:", layout="wide")

# Landing Page
def landing_page():
    st.title(":briefcase: SmartMatch - Recruitment Assistant")
    st.write("Welcome to SmartMatch! This platform streamlines the recruitment process, from resume parsing to candidate matching and interview scheduling.")
    st.markdown("---")
    
    # Overview sections in columns
    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader(":clipboard: Overview")
        st.write("Gain insights into the recruitment process, view current job openings, candidate status, and performance metrics.")
    with col2:
        st.subheader(":busts_in_silhouette: Candidate Matching")
        st.write("Match candidates to specific job openings based on skills and experience, making hiring decisions faster and more accurate.")
    with col3:
        st.subheader(":calendar: Interview Scheduling")
        st.write("Seamlessly manage interview schedules and track the progress of each candidate in the recruitment pipeline.")
    
    st.markdown("---")
    st.header("Choose Your Role")
    
    # Role selection buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("RECRUITER"):
            st.session_state['page'] = 'recruiter_login'
            st.rerun()
        if st.button("STUDENT"):
            st.session_state['page'] = 'student_login'
            st.rerun()



# Recruiter Login Page
def recruiter_login():
    st.title(":office_worker: Recruiter Login")
    recruiter_code = st.text_input("Recruiter Code")
    password = st.text_input("Password", type="password")
    
    # Login and Registration Buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Login"):
            if validate_recruiter(recruiter_code, password):
                st.session_state['page'] = 'recruiter_dashboard'
                st.session_state['recruiter_code'] = recruiter_code
                st.rerun()
            else:
                st.error("Invalid recruiter code or password.")
    with col2:
        if st.button("Register as Recruiter"):
            st.session_state['page'] = 'recruiter_registration'
            st.rerun()
    with col3:
        if st.button("Back to Home"):
            st.session_state['page'] = 'landing'
            st.rerun()

# Recruiter Registration Page
def recruiter_registration():
    
    st.title("Recruiter Registration")
    new_recruiter_code = st.text_input("Create Recruiter Code")
    new_password = st.text_input("Create Password", type="password")
    new_email = st.text_input("Email Address")
    
    if st.button("Register"):
        if new_recruiter_code and new_password:
            add_recruiter(new_recruiter_code, new_password, new_email)
            st.success("Recruiter registered successfully!")
        else:
            st.error("Please enter both code and password.")
    
    # Back to Login Page button
    if st.button("Back to Login Page"):
        st.session_state['page'] = 'recruiter_login'
        st.rerun()


def recruiter_dashboard():
    st.title(":office_worker: RECRUITER Dashboard")
    st.write(f"Welcome, Recruiter! Manage candidates, review profiles, and match with ideal candidates.")
    st.markdown("---")

    # Job Openings Section with Save and Delete Features
    recruiter_code = st.session_state["recruiter_code"]
    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("Job Openings")
        st.write("Post job openings, filter based on qualifications, and manage each candidate's status in the hiring pipeline.")

        # Fetch previously uploaded job descriptions
        previous_descriptions = get_job_descriptions(recruiter_code)

        # Dropdown for previously uploaded job descriptions
        selected_title = None
        if previous_descriptions:
            selected_title = st.selectbox(
                "Select a previously uploaded job description by title",
                options=list(previous_descriptions.keys()),
                key="description_select"
            )
            if selected_title:
                with st.expander(f"**View Job Description: {selected_title}**", expanded=False):
                    st.write(previous_descriptions[selected_title])  # Display JD description
                with st.expander(f"**Required Skills: {selected_title}**", expanded=False):
                    # Fetch and display skills from the database
                    conn = connect_db()
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT jd.skills FROM job_descriptions jd JOIN recruiters r ON jd.recruiter_id = r.recruiter_id WHERE r.recruiter_code = ? AND jd.title = ?",
                        (recruiter_code, selected_title)
                    )
                    skills_result = cursor.fetchone()
                
                    if skills_result and skills_result[0]:
                        st.markdown("**Extracted Skills:**")
                        st.write(skills_result[0])  # Display comma-separated skills
                    else:
                        st.info("No skills found for this job description.")
                    conn.close()
                    

        # Add Job Description Title
        job_title = st.text_input("**Add new job opening**", placeholder="e.g., Software Engineer Intern", key="job_title")

        # Option to paste or upload job description
        job_description_option = st.radio(
            "How would you like to add the job description?",
            ("Paste text", "Upload PDF"),
            key="description_option"
        )

        job_description = ""
        if job_description_option == "Paste text":
            job_description = st.text_area("Paste job description here", key="text_description")
        elif job_description_option == "Upload PDF":
            uploaded_file = st.file_uploader("Upload job description PDF", type="pdf", key="pdf_upload")
            if uploaded_file:
                job_description = extract_text_from_pdf(uploaded_file)
                if job_description:
                    st.write("**Extracted Job Description:**")
                    st.text_area("Extracted text from your uploaded job description:", value=job_description, height=200, disabled=True)
                else:
                    st.error("Could not extract text. Ensure the PDF contains selectable text or use an OCR-enabled PDF.")

        # Save Job Description Button
        if job_title and job_description and st.button("Save Job Description", key="save_button"):
            # Skills list to compare
            extracted_skills = extract_skills(job_description, skills_list)
            
            # Save job description and extracted skills
            if save_job_description(recruiter_code, job_title, job_description, uploaded_file, extracted_skills):
                st.success("Job description saved successfully!")
                st.rerun()
            else:
                st.error("Failed to save job description. Please try again.")

        # Delete All Job Descriptions Button
        if previous_descriptions and st.button("Delete All Job Descriptions"):
            delete_all_job_descriptions(recruiter_code)
            st.success("All job descriptions deleted successfully!")
            st.rerun()

    with col2:
        st.subheader("Review Resumes")
        st.write("View candidate profiles and review their skills and experience.")

        if selected_title:
            # Fetch resumes for the selected job description
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT s.student_code, s.name, rr.resume_text, rr.timestamp
                FROM recruiter_resumes rr
                JOIN students s ON rr.student_code = s.student_code
                WHERE rr.jd_title = ? AND rr.recruiter_code = ?
                """,
                (selected_title, recruiter_code)
            )
            resumes = cursor.fetchall()

            if resumes:
                for student_code, name, resume_text, timestamp in resumes:
                    with st.expander(f"**{name} (Student ID: {student_code})**"):
                        st.write(f"**Submitted on:** {timestamp}")
                        st.write(f"**Resume:**\n{resume_text}")
            else:
                st.info("No resumes have been submitted for the selected job description.")
        else:
            st.info("Select a job description to view the corresponding resumes.")

    with col3:
        st.subheader("AI Recruiter Assistant")
        st.write("Chat with the recruiter bot for automated insights and assistance.")

    st.markdown("---")

    col4, col5  = st.columns(2)
    with col4:
        import pandas as pd
        from sentence_transformers import SentenceTransformer
        from sklearn.metrics.pairwise import cosine_similarity
        import numpy as np

        with col4:
            st.subheader("Shortlist Candidates")
            st.write("Match candidates to specific job openings based on skills and experience, making hiring decisions faster and more accurate.")

            # if selected_title:
            #     st.write(f"**Job Description:** {selected_title}")
            #     jd_text = previous_descriptions[selected_title]  # Fetch JD text

            #     # Fetch resumes for the selected JD
            #     conn = connect_db()
            #     cursor = conn.cursor()
            #     cursor.execute(
            #         """
            #         SELECT s.student_code, s.name, rr.resume_text
            #         FROM recruiter_resumes rr
            #         JOIN students s ON rr.student_code = s.student_code
            #         WHERE rr.jd_title = ? AND rr.recruiter_code = ?
            #         """,
            #         (selected_title, recruiter_code)
            #     )
            #     resumes = cursor.fetchall()
                
            #     if resumes:
            #         # Extract resume texts
            #         resume_data = [{"Student ID": r[0], "Name": r[1], "Resume": r[2]} for r in resumes]
            #         resume_df = pd.DataFrame(resume_data)

            #         # Initialize embedding model
            #         model = SentenceTransformer("all-MiniLM-L6-v2", cache_folder=r'D:\models')

            #         # Compute embeddings for JD and resumes
            #         jd_embedding = model.encode([jd_text], convert_to_tensor=True)
            #         resume_embeddings = model.encode(resume_df["Resume"].tolist(), convert_to_tensor=True)

            #         # Calculate cosine similarities
            #         similarities = cosine_similarity(jd_embedding, resume_embeddings).flatten()
            #         resume_df["Skill Similarity"] = np.round(similarities * 100, 2)  # Convert to percentage

            #         # Display the table with similarity scores
            #         st.write("**Resumes with Skill Similarity:**")
            #         st.dataframe(resume_df[["Student ID", "Name", "Skill Similarity"]].sort_values("Skill Similarity", ascending=False))
            #     else:
            #         st.info("No resumes submitted for the selected job description.")
            # else:
            #     st.info("Select a job description to view the corresponding resumes.")
    

    with col5:
        st.subheader("Schedule Interviews")
        st.write("Seamlessly schedule interviews using Google Meet and Calendar integration.")

    
    st.markdown("---")

    # Logout button
    if st.button("Logout", key="logout_button"):
        st.session_state["page"] = "landing"
        st.session_state.pop("recruiter_code", None)
        st.rerun()

# Helper function to extract text from a PDF
def extract_text_from_pdf(uploaded_file):
    try:
        pdf_text = ""
        # Load the PDF file
        # with pdfplumber.open(BytesIO(uploaded_file.read())) as pdf:
        #     for page in pdf.pages:
        #         pdf_text += page.extract_text() or ""
        
        with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
            for page in doc:
                pdf_text += page.get_text() 

        # If no text was extracted, use OCR for images/scans
        # if not pdf_text.strip():
        #     pdf_text = ocr_pdf(uploaded_file)
        return pdf_text
    except Exception as e:
        st.error("Error reading PDF file.")
        return None

# OCR function for image-based PDFs
# def ocr_pdf(uploaded_file):
#     pdf_images = []
#     with pdfplumber.open(BytesIO(uploaded_file.read())) as pdf:
#         for page in pdf.pages:
#             img = page.to_image()
#             pdf_images.append(img)

#     # Run OCR on each page image
#     ocr_text = ""
#     for img in pdf_images:
#         ocr_text += pytesseract.image_to_string(img)
#     return ocr_text
# Student Page

def student_dashboard():
    # Display a welcome message with the student's name
    if "student_name" in st.session_state:
        st.title(f":mortar_board: Welcome, {st.session_state['student_name']}!")
    else:
        st.title(":mortar_board: STUDENT Dashboard")
        st.warning("Please log in to see your details.")
        return  # Stop execution if the student is not logged in

    # Fetch student code for database operations
    student_code = st.session_state.get("student_code")

    # Recruiter Matching Section
    recruiter_code = st.text_input("Enter Recruiter Code to Connect")
    recruiter_email = None
    job_descriptions = []

    if recruiter_code:
        if recruiter_exists(recruiter_code):
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("SELECT email FROM recruiters WHERE recruiter_code = ?", (recruiter_code,))
            result = cursor.fetchone()

            if result:
                recruiter_email = result[0]
                st.success("Recruiter found.")

                # Fetch Job Descriptions for the connected recruiter
                cursor.execute(
                    """
                    SELECT jd.id, jd.title, jd.description
                    FROM job_descriptions jd
                    INNER JOIN recruiters r ON jd.recruiter_id = r.recruiter_id
                    WHERE r.recruiter_code = ?
                    """,
                    (recruiter_code,)
                )
                job_descriptions = cursor.fetchall()

            else:
                st.error("Recruiter email not found.")
        else:
            st.error("Invalid recruiter code.")

    st.markdown("---")

    # Fetch previously stored resume text
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT pdf_location FROM students WHERE student_code = ?", (student_code,))
    result = cursor.fetchone()
    previous_text = result[0] if result else None

    # Columns for Resume Handling and Recruiter Contact
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Your Resume Text")
        if previous_text:
            st.text_area("Previously Uploaded Resume Text", value=previous_text, height=200, disabled=True)
        else:
            st.info("No resume text found. Please upload your resume.")

        uploaded_file = st.file_uploader("Upload your Resume (PDF only):", type=["pdf"])

        if uploaded_file:
            try:
                # Extract text from uploaded PDF using pdfplumber
                pdf_text = ""
                with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
                    for page in doc:
                        pdf_text += page.get_text() 

                if pdf_text.strip():
                    # Save extracted text into the student's `pdf_location` field
                    cursor.execute(
                        "UPDATE students SET pdf_location = ? WHERE student_code = ?",
                        (pdf_text, student_code),
                    )
                    conn.commit()

                    # Display extracted text
                    st.markdown("### Extracted Resume Text")
                    st.text_area("Extracted text from your uploaded resume:", value=pdf_text, height=200, disabled=True)

                    st.success("Resume text successfully extracted and saved.")
                else:
                    st.error("The uploaded PDF is empty or unreadable.")
            except Exception as e:
                st.error(f"An error occurred while processing the PDF: {str(e)}")

        # Display available job descriptions (if any)
        if job_descriptions:
            st.subheader("Available Job Descriptions from Recruiter")
            jd_options = {jd[1]: f"{jd[1]} - {jd[2][:50]}..." for jd in job_descriptions}  # JD title and short description
            selected_jd_title = st.selectbox("Select a Job Description to Apply For", jd_options.keys(), format_func=lambda x: jd_options[x])
        else:
            selected_jd_title = None


        # Button to send resume to recruiter
        if st.button("Send Resume to Recruiter"):
            if recruiter_code and previous_text and selected_jd_title:
                # Check if a record already exists with the title instead of jd_id
                cursor.execute(
                    "SELECT COUNT(*) FROM recruiter_resumes WHERE recruiter_code = ? AND student_code = ? AND jd_title = ?",
                    (recruiter_code, student_code, selected_jd_title),
                )
                record_exists = cursor.fetchone()[0]

                if record_exists:
                    st.warning("You have already sent your resume for this job description.")
                else:
                    # Insert the new record with the job description title
                    cursor.execute(
                        "INSERT INTO recruiter_resumes (recruiter_code, student_code, resume_text, jd_title) VALUES (?, ?, ?, ?)",
                        (recruiter_code, student_code, previous_text, selected_jd_title),
                    )
                    conn.commit()
                    st.success("Your resume has been sent to the recruiter for the selected job description.")
            else:
                st.error("Please upload a resume, connect with a recruiter, and select a job description before sending.")

    with col2:
        st.subheader("Contact Recruiter")
        if recruiter_email:
            st.write(f"Compose an email to the recruiter below. Email: {recruiter_email}")
            email_body = st.text_area("Write your email message:", placeholder="Type your message here...", label_visibility='hidden')

            if st.button("Send Email"):
                if email_body.strip():
                    # Construct Gmail-specific URL
                    gmail_url = (
                        f"https://mail.google.com/mail/?view=cm&fs=1&to={recruiter_email}"
                        f"&su=Job Inquiry&body={email_body}"
                    )
                    # Open Gmail in the browser's new tab
                    st.markdown(
                        f'<a href="{gmail_url}" target="_blank">Click here to send the email</a>',
                        unsafe_allow_html=True
                    )
                else:
                    st.error("Email body cannot be empty.")

    conn.close()

    st.markdown("---")

    # Back to Home button
    if st.button("Back to Home"):
        st.session_state['page'] = 'landing'
        st.rerun()


# Student Login Page
def student_login():
    st.title(":mortar_board: Student Login")
    
    # Login Fields
    student_code = st.text_input("Student Code", key="student_code_input")
    password = st.text_input("Password", type="password", key="password_input")
    
    # Login and Navigation Buttons
    col1, col2, col3 = st.columns(3)
    
    # Login Logic
    with col1:
        if st.button("Login"):
            if validate_student(student_code, password):
                # Fetch student name
                conn = connect_db()
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT name FROM students WHERE student_code = ?",
                    (student_code,)
                )
                result = cursor.fetchone()
                conn.close()

                if result:
                    st.session_state['student_name'] = result[0]  # Store student name
                    st.session_state['student_code'] = student_code  # Store student code
                    st.session_state['page'] = 'student_dashboard'  # Navigate to dashboard
                    st.success(f"Welcome, {result[0]}!")
                    st.rerun()
                else:
                    st.error("Error fetching student details. Please contact support.")
            else:
                st.error("Invalid student code or password.")
    
    # Registration Button
    with col2:
        if st.button("Register as Student"):
            st.session_state['page'] = 'student_registration'
            st.rerun()
    
    # Back to Home Button
    with col3:
        if st.button("Back to Home"):
            st.session_state['page'] = 'landing'
            st.rerun()

# Student Registration Page
def student_registration():
    st.title(":mortar_board: Student Registration")
    
    # Registration Fields
    name = st.text_input("Full Name")
    student_code = st.text_input("Create Student Code")
    password = st.text_input("Create Password", type="password")
    email = st.text_input("Email Address")
    
    # Registration Button
    if st.button("Register"):
        if name and student_code and password and email:
            if not student_exists(student_code):  # Check if the student code is unique
                add_student(student_code, name, password, email)
                st.success("Student registered successfully!")
            else:
                st.error("Student code already exists. Please choose a different code.")
        else:
            st.error("Please fill out all fields.")
    
    # Back to Login Page Button
    if st.button("Back to Login Page"):
        st.session_state['page'] = 'student_login'
        st.rerun()

# Main logic for handling pages
if 'page' not in st.session_state:
    st.session_state['page'] = 'landing'

if st.session_state['page'] == 'landing':
    landing_page()
elif st.session_state['page'] == 'recruiter_login':
    recruiter_login()
elif st.session_state['page'] == 'recruiter_registration':
    recruiter_registration()
elif st.session_state['page'] == 'recruiter_dashboard':
    recruiter_dashboard()
elif st.session_state['page'] == 'student_login':
    student_login()
elif st.session_state['page'] == 'student_registration':
    student_registration()
elif st.session_state['page'] == 'student_dashboard':
    student_dashboard()
