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
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from database_func import add_recruiter, validate_recruiter, recruiter_exists, get_job_descriptions, save_job_description, delete_all_job_descriptions, student_exists, add_student, validate_student, connect_db, extract_skills#, delete_job_description  # Import functions from the database module

with open("extractor_library.json", "r") as file:
    skills_data = json.load(file)

skills_list = skills_data["skills_list"]

import google.generativeai as genai
genai.configure(api_key=os.environ['GEMINI_API_KEY'])




def gemini_embedding(text):
    
    response = genai.embed_content(content=text, model="models/text-embedding-004")
    return response['embedding']


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
    col1, col2, col3 = st.columns([2, 1.5, 3])

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
                        # st.markdown("**Extracted Skills:**")
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
        st.subheader("Shortlist Candidates")
        st.write("Match candidates to specific job openings based on skills and experience, making hiring decisions faster and more accurate.")

        if selected_title:
            st.write(f"**Job Description:** {selected_title}")
            jd_text = previous_descriptions[selected_title]  # Fetch JD text

            # Fetch resumes for the selected JD
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT s.student_code, s.name, rr.resume_text
                FROM recruiter_resumes rr
                JOIN students s ON rr.student_code = s.student_code
                WHERE rr.jd_title = ? AND rr.recruiter_code = ?
                """,
                (selected_title, recruiter_code)
            )
            resumes = cursor.fetchall()

            if resumes:
                # Extract resume texts
                resume_data = [{"Student ID": r[0], "Name": r[1], "Resume": r[2]} for r in resumes]

                # Compute embeddings for JD and resumes using Gemini API
                # jd_embedding = gemini_embedding(jd_text)  # Use the embedding function
                jd_skills = extract_skills(jd_text, skills_list)  # Extract JD skills
                jd_skills_text = ", ".join(jd_skills)
                jd_embedding = gemini_embedding(jd_skills_text)

                resume_scores = []

                for r in resume_data:
                    # resume_embedding = gemini_embedding(r["Resume"])
                    # similarity = cosine_similarity([jd_embedding], [resume_embedding])[0][0] * 100

                    # Extract skills from the resume
                    resume_skills = extract_skills(r["Resume"], skills_list)
                    resume_skills_text = ", ".join(resume_skills)
                    resume_embedding = gemini_embedding(resume_skills_text)

                    similarity = cosine_similarity([jd_embedding], [resume_embedding])[0][0]*100

                    matching_skills = ", ".join(set(jd_skills).intersection(resume_skills))

                    resume_scores.append({
                        "Student ID": r["Student ID"],
                        "Name": r["Name"],
                        "Resume": r["Resume"],
                        "Resume Score": round(similarity, 2),
                        "Matching Skills": matching_skills
                    })

                # Display the table with resume scores and matching skills
                st.write("**Resumes with Resume Scores and Matching Skills:**")

                resume_df = pd.DataFrame(resume_scores)
                st.dataframe(resume_df[["Student ID", "Name", "Resume Score", "Matching Skills"]].sort_values("Resume Score", ascending=False), use_container_width=True)
            else:
                st.info("No resumes submitted for the selected job description.")
        else:
            st.info("Select a job description to view the corresponding resumes.")


    with col5:
        st.subheader("Contact Selected Candidates")
        st.write("Notify shortlisted candidates about interviews via email.")

        if selected_title:
            # Fetch candidates for the selected job description
            cursor.execute(
                """
                SELECT s.student_code, s.name, s.email
                FROM recruiter_resumes rr
                JOIN students s ON rr.student_code = s.student_code
                WHERE rr.jd_title = ? AND rr.recruiter_code = ?
                """,
                (selected_title, recruiter_code)
            )
            candidates = cursor.fetchall()
            cursor.execute('SELECT email FROM recruiters WHERE recruiter_code = ?', (recruiter_code,))
            recruiter_email = cursor.fetchone()[0]

            if candidates:
                # Prepare candidate data
                candidate_data = [{"Student ID": c[0], "Name": c[1], "Email": c[2]} for c in candidates]
                candidate_df = pd.DataFrame(candidate_data)
                candidate_df["Select"] = False

                # Display candidates with checkboxes
                for idx, row in candidate_df.iterrows():
                    candidate_df.loc[idx, "Select"] = st.checkbox(f"Select {row['Name']}", key=f"candidate_{row['Student ID']}")

                # Filter selected candidates
                selected_candidates = candidate_df[candidate_df["Select"]]
                if not selected_candidates.empty:
                    st.write("Selected Candidates:")
                    st.dataframe(selected_candidates[["Student ID", "Name", "Email"]], use_container_width=True)

                    # Predefined email body
                    gmeet_link = "https://meet.google.com/example-link"  # Replace with your Gmeet generation logic
                    # email_body = f"""
                    # Hello,\n
                    # You have been shortlisted for an interview for the job role {selected_title}.\n
                    # Please join the meeting using the link below:
                    # Google Meet Link: {gmeet_link}\n\n
                    # Best regards,\n{recruiter_email}
                    # """

                    email_body = f"Hello,\nYou have been shortlisted for an interview for the job role {selected_title}.\nPlease join the meeting using the link below:\nGoogle Meet Link: {gmeet_link} \nRegards"
                    body = st.text_area("Write your email message:", placeholder="Type your message here...", label_visibility='hidden', value=email_body.strip(), height=200, disabled=False)


                    # Display the email body
                    # body = st.text_area("Email Content", value=email_body.strip(), height=200, disabled=False)

                    if st.button("Send Email"):
                        # Prepare Gmail link
                        recipient_emails = ",".join(selected_candidates["Email"].tolist())
                        
                        gmail_url = (
                            f"https://mail.google.com/mail/?view=cm&fs=1&to={recipient_emails}"
                            f"&su=Interview Invite for {selected_title}&body={body}"
                        )
                        # Open Gmail in the browser's new tab
                        st.markdown(
                            f'<a href="{gmail_url}" target="_blank">Click here to send the email</a>',
                            unsafe_allow_html=True
                        )
                        
                else:
                    st.info("Select at least one candidate to notify.")
            else:
                st.info("No candidates available for the selected job description.")
        else:
            st.info("Select a job description to view and notify candidates.")

    
    st.markdown("---")
    # Logout button
    if st.button("Logout", key="logout_button"):
        st.session_state["page"] = "landing"
        st.session_state.pop("recruiter_code", None)
        st.rerun()
def generate_gmeet_link():
    return "https://meet.google.com/new"




# Helper function to extract text from a PDF
def extract_text_from_pdf(uploaded_file):
    try:
        pdf_text = ""
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
                st.success("Recruiter found. Fetching job descriptions...")

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
    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("Your Resume Text")
        if previous_text:
            st.text_area("Previously Uploaded Resume Text", value=previous_text, height=200, disabled=True)
        else:
            st.info("No resume text found. Please upload your resume.")

        uploaded_file = st.file_uploader("Upload your Resume (PDF only):", type=["pdf"])

        if uploaded_file:
            try:
                # Extract text from uploaded PDF
                pdf_text = ""
                with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
                    for page in doc:
                        pdf_text += page.get_text()

                if pdf_text.strip():
                    # Extract skills from resume text
                    extracted_skills = []
                    if skills_list:
                        extracted_skills = extract_skills(pdf_text, skills_list)
                    extracted_skills = list(set(extracted_skills))
                    extracted_skills_str = ", ".join(extracted_skills)

                    # Save extracted text and skills into the student's `pdf_location` field
                    cursor.execute(
                        "UPDATE students SET pdf_location = ? WHERE student_code = ?",
                        (pdf_text, student_code),
                    )
                    conn.commit()

                    # Display extracted text and skills
                    st.markdown("### Extracted Resume Text")
                    st.text_area("Extracted text from your uploaded resume:", value=pdf_text, height=200, disabled=True)

                    st.markdown("### Extracted Skills from Resume")
                    st.write(extracted_skills_str)

                    st.success("Resume text and skills successfully extracted and saved.")
                else:
                    st.error("The uploaded PDF is empty or unreadable.")
            except Exception as e:
                st.error(f"An error occurred while processing the PDF: {str(e)}")

        # Display available job descriptions
        if job_descriptions:
            st.subheader("Available Job Descriptions from Recruiter")
            jd_options = {jd[1]: f"{jd[1]} - {jd[2][:50]}..." for jd in job_descriptions}  # JD title and short description
            selected_jd_title = st.selectbox("Select a Job Description to Apply For", jd_options.keys(), format_func=lambda x: jd_options[x])
        else:
            selected_jd_title = None

        # Buttons for sending and withdrawing applications
        col_apply, col_withdraw = st.columns(2)

        with col_apply:
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
                        # Insert the new record with the job description title and extracted skills
                        cursor.execute(
                            """
                            INSERT INTO recruiter_resumes 
                            (recruiter_code, student_code, resume_text, jd_title, extracted_resume_skills) 
                            VALUES (?, ?, ?, ?, ?)
                            """,
                            (recruiter_code, student_code, previous_text, selected_jd_title, extracted_skills_str),
                        )
                        conn.commit()
                        st.success("Your resume and extracted skills have been sent to the recruiter for the selected job description.")
                else:
                    st.error("Please upload a resume, connect with a recruiter, and select a job description before sending.")

        with col_withdraw:
            if st.button("Withdraw Application"):
                if recruiter_code and selected_jd_title:
                    # Check if a record exists to withdraw
                    cursor.execute(
                        "SELECT COUNT(*) FROM recruiter_resumes WHERE recruiter_code = ? AND student_code = ? AND jd_title = ?",
                        (recruiter_code, student_code, selected_jd_title),
                    )
                    record_exists = cursor.fetchone()[0]

                    if record_exists:
                        # Delete the record for the selected job description
                        cursor.execute(
                            "DELETE FROM recruiter_resumes WHERE recruiter_code = ? AND student_code = ? AND jd_title = ?",
                            (recruiter_code, student_code, selected_jd_title),
                        )
                        conn.commit()
                        st.success("Your application for the selected job description has been withdrawn.")
                    else:
                        st.warning("No application found to withdraw for the selected job description.")
                else:
                    st.error("Please connect with a recruiter and select a job description to withdraw your application.")

    with col2:
        st.subheader("Match your Resume to a Job Description")
        st.write(
            "Select job descriptions from your recruiter and match your resume to them. "
            "This will help you find the best fit for your skills and experience."
        )

        if recruiter_code:
            # Validate recruiter existence
            if recruiter_exists(recruiter_code):
                # Fetch job descriptions for the recruiter
                conn = connect_db()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT title, skills 
                    FROM job_descriptions 
                    JOIN recruiters ON job_descriptions.recruiter_id = recruiters.recruiter_id 
                    WHERE recruiters.recruiter_code = ?
                """, (recruiter_code,))
                job_descriptions = cursor.fetchall()

                # Fetch the student's resume
                student_code = st.session_state.get("student_code")
                cursor.execute("SELECT pdf_location FROM students WHERE student_code = ?", (student_code,))
                result = cursor.fetchone()
                conn.close()

                if not result or not result[0]:
                    st.error("No resume uploaded. Please upload your resume first.")
                else:
                    # Extract student's skills from their resume
                    resume_text = result[0]
                    student_skills = extract_skills(resume_text, skills_list)

                    if not student_skills:
                        st.warning("No skills could be extracted from your resume.")
                    else:
                        # Calculate compatibility
                        compatibility_data = []
                        student_embedding = gemini_embedding(", ".join(student_skills)) 
                        for jd_title, jd_skills in job_descriptions:
                            jd_skills_list = jd_skills.split(", ") if jd_skills else []
                            jd_embedding = gemini_embedding(", ".join(jd_skills_list)) 

                            common_skills = set(student_skills).intersection(set(jd_skills_list))
                            compatibility_score = round(len(common_skills) / len(jd_skills_list) * 100, 2) if jd_skills_list else 0
                            abs_compatibility = '✅' if compatibility_score >= 10 else '❌'

                            similarity = cosine_similarity([student_embedding], [jd_embedding])[0][0] * 100

                        # Compute cosine similarity
                            compatibility_data.append({
                                "Job Title": jd_title,
                                "Required Skills": ", ".join(jd_skills_list),
                                # "Your Skills": ", ".join(student_skills),
                                "Common Skills": ", ".join(common_skills),
                                "Compatibility": abs_compatibility,
                                "Resume Score": round(similarity, 2)
                            })
                        st.write('**Your Skills:**')
                        st.write(', '.join(student_skills))
                        # Display results in a tabular format
                        if compatibility_data:
                            import pandas as pd
                            compatibility_df = pd.DataFrame(compatibility_data)
                            st.dataframe(compatibility_df[['Job Title', 'Required Skills', 'Common Skills', 'Compatibility', 'Resume Score']].sort_values(by='Resume Score', ascending=False) , use_container_width=True)
                        else:
                            st.info("No job descriptions found or no compatible skills.")
            else:
                st.error("Invalid recruiter code.")
        else:
            st.info("Please enter a recruiter code to proceed.")


    conn.close()

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
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

    with col2:
        st.subheader("AI student support")
        if st.button("Chat with AI"):
            None
    st.markdown('---')
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
