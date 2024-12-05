import streamlit as st
import fitz
import pytesseract
from PIL import Image
import sqlite3
import os
import shutil
import atexit
import time
import re
import json
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from database_func import add_recruiter, validate_recruiter, recruiter_exists, get_job_descriptions, save_job_description, delete_all_job_descriptions, student_exists, add_student, validate_student, connect_db, extract_skills#, delete_job_description  # Import functions from the database module
from chroma_db_func import index_database_data_for_student, index_database_data_for_recruiter, GeminiEmbeddingFunction
import chromadb
# from chromadb.utils import embedding_functions
from chromadb.config import Settings

settings = Settings(
    persist_directory=r"./chroma_db"  
)

import google.generativeai as genai


with open("extractor_library.json", "r") as file:
    skills_data = json.load(file)

skills_list = skills_data["skills_list"]



genai.configure(api_key=os.environ['GEMINI_API_KEY'])
def gemini_embedding(text):
    
    response = genai.embed_content(content=text, model="models/text-embedding-004")
    return response['embedding']



st.set_page_config(page_title="SmartMatch", page_icon=":briefcase:", layout="wide")

# Landing Page
def landing_page():
    st.title(":briefcase: SmartMatch - Recruitment Assistant")
    st.write("Welcome to SmartMatch! This platform streamlines the recruitment process, from resume parsing to candidate matching and interview scheduling.")
    st.markdown("---")
    
    # Overview sections in columns
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.subheader(":clipboard: Overview")
        st.write("Gain insights into the recruitment process, view current job openings, candidate status, and performance metrics.")
    with col2:
        st.subheader(":busts_in_silhouette: Candidate Matching")
        st.write("Match candidates to specific job openings based on skills and experience, making hiring decisions faster and more accurate.")
    with col3:
        st.subheader(":calendar: Interview Scheduling")
        st.write("Seamlessly manage interview schedules and track the progress of each candidate in the recruitment pipeline.")
    with col4:
        st.subheader(":robot_face: AI chat assistant")
        st.write("Engage with AI chat assistant to get quick answers about resumes and job posting details.")
    st.markdown("---")
    st.header("Choose Your Role")
    
    
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
    
    
    if st.button("Back to Login Page"):
        st.session_state['page'] = 'recruiter_login'
        st.rerun()


def recruiter_dashboard():
    st.title(":office_worker: RECRUITER Dashboard")
    st.write(f"Welcome, Recruiter! Manage candidates, review profiles, and match with ideal candidates.")
    st.markdown("---")

    
    recruiter_code = st.session_state["recruiter_code"]
    col1, col2, col3 = st.columns([2, 1.5, 3])

    with col1:
        st.subheader("Job Openings")
        st.write("Post job openings, filter based on qualifications, and manage each candidate's status in the hiring pipeline.")

        
        previous_descriptions = get_job_descriptions(recruiter_code)

        selected_title = None
        if previous_descriptions:
            selected_title = st.selectbox(
                "Select a previously uploaded job description by title",
                options=list(previous_descriptions.keys()),
                key="description_select"
            )
            if selected_title:
                with st.expander(f"**View Job Description: {selected_title}**", expanded=False):
                    st.write(previous_descriptions[selected_title])  
                with st.expander(f"**Required Skills: {selected_title}**", expanded=False):
                    
                    conn = connect_db()
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT jd.skills FROM job_descriptions jd JOIN recruiters r ON jd.recruiter_id = r.recruiter_id WHERE r.recruiter_code = ? AND jd.title = ?",
                        (recruiter_code, selected_title)
                    )
                    skills_result = cursor.fetchone()
                
                    if skills_result and skills_result[0]:
                        st.write(skills_result[0])
                    else:
                        st.info("No skills found for this job description.")
                    conn.close()
                    


        job_title = st.text_input("**Add new job opening**", placeholder="e.g., Software Engineer Intern", key="job_title")


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


        if job_title and job_description and st.button("Save Job Description", key="save_button"):

            extracted_skills = extract_skills(job_description, skills_list)
            
 
            if save_job_description(recruiter_code, job_title, job_description, uploaded_file, extracted_skills):
                st.success("Job description saved successfully!")
                st.rerun()
            else:
                st.error("Failed to save job description. Please try again.")


        if previous_descriptions and st.button("Delete All Job Descriptions"):
            delete_all_job_descriptions(recruiter_code)
            st.success("All job descriptions deleted successfully!")
            st.rerun()

    with col2:
        st.subheader("Review Resumes")
        st.write("View candidate profiles and review their skills and experience.")

        if selected_title:
         
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

        st.subheader("Shortlist Candidates")
        st.write("Match candidates to specific job openings based on their relevant skills and resume scores.")

        if selected_title:
            st.write(f"**Job Description:** {selected_title}")
            jd_text = previous_descriptions[selected_title]

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
                
                resume_data = [{"Student ID": r[0], "Name": r[1], "Resume": r[2]} for r in resumes]

                
                # jd_embedding = gemini_embedding(jd_text) 
                jd_skills = extract_skills(jd_text, skills_list) 
                jd_skills_text = ", ".join(jd_skills)
                jd_embedding = gemini_embedding(jd_skills_text)

                resume_scores = []

                for r in resume_data:
                    # resume_embedding = gemini_embedding(r["Resume"])
                    # similarity = cosine_similarity([jd_embedding], [resume_embedding])[0][0] * 100


                    resume_skills = extract_skills(r["Resume"], skills_list)
                    resume_skills_text = ", ".join(resume_skills)
                    resume_embedding = gemini_embedding(resume_skills_text)

                    similarity = cosine_similarity([jd_embedding], [resume_embedding])[0][0]*100
                    compatibility = '✅' if similarity >= 70 else '❌'

                    matching_skills = ", ".join(set(jd_skills).intersection(resume_skills))

                    resume_scores.append({
                        "Student ID": r["Student ID"],
                        "Name": r["Name"],
                        # "Resume": r["Resume"],
                        "Resume Score": round(similarity, 2),
                        "Compatibility": compatibility,
                        "Matching Skills": matching_skills
                    })


                st.write("**Resumes with Resume Scores and Matching Skills:**")

                resume_df = pd.DataFrame(resume_scores)
                st.dataframe(resume_df[["Student ID", "Name", "Resume Score", "Compatibility", "Matching Skills"]].sort_values("Resume Score", ascending=False), use_container_width=True)
            else:
                st.info("No resumes submitted for the selected job description.")
        else:
            st.info("Select a job description to view the corresponding resumes.")


    st.markdown("---")

    col4, col5  = st.columns([2, 4.5])

    with col4:
        st.subheader("Contact Selected Candidates")
        st.write("Notify shortlisted candidates about interviews via email.")

        if selected_title:
            
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
              
                candidate_data = [{"Student ID": c[0], "Name": c[1], "Email": c[2]} for c in candidates]
                candidate_df = pd.DataFrame(candidate_data)
                candidate_df["Select"] = False

                
                for idx, row in candidate_df.iterrows():
                    candidate_df.loc[idx, "Select"] = st.checkbox(f"Select {row['Name']}", key=f"candidate_{row['Student ID']}")

              
                selected_candidates = candidate_df[candidate_df["Select"]]
                if not selected_candidates.empty:
                    st.write("Selected Candidates:")
                    st.dataframe(selected_candidates[["Student ID", "Name", "Email"]], use_container_width=True)

                    # email body
                    gmeet_link = "https://meet.google.com/example-link"  
                    # email_body = f"""
                    # Hello,\n
                    # You have been shortlisted for an interview for the job role {selected_title}.\n
                    # Please join the meeting using the link below:
                    # Google Meet Link: {gmeet_link}\n\n
                    # Best regards,\n{recruiter_email}
                    # """

                    email_body = f"Hello,\nYou have been shortlisted for an interview for the job role {selected_title}.\nPlease join the meeting using the link below:\nGoogle Meet Link: {gmeet_link} \nRegards"
                    body = st.text_area("Write your email message:", placeholder="Type your message here...", label_visibility='hidden', value=email_body.strip(), height=200, disabled=False)


                    
                    # body = st.text_area("Email Content", value=email_body.strip(), height=200, disabled=False)

                    if st.button("Send Email"):
                        
                        recipient_emails = ",".join(selected_candidates["Email"].tolist())
                        
                        gmail_url = (
                            f"https://mail.google.com/mail/?view=cm&fs=1&to={recipient_emails}"
                            f"&su=Interview Invite for {selected_title}&body={body}"
                        )
                        
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



    with col5:
        if "chat_history" not in st.session_state:
            st.session_state["chat_history"] = []

        st.subheader("AI Recruiter Support Chat")
        
        user_query = st.text_area("Ask about candidates' resumes or job descriptions:", placeholder="Chat with gemini-1.5-flash-8b")

        embedding_function = GeminiEmbeddingFunction()

        if recruiter_code:
            global recruiter_client
            recruiter_client = chromadb.PersistentClient(path="chroma_db_recruiter")
            collection = recruiter_client.get_or_create_collection(
                name=f"recruiter_{recruiter_code}",
                embedding_function=embedding_function
            )

           
            collection_count = collection.count()
            if collection_count == 0:
                st.write("Indexing data for recruiter...")
                index_database_data_for_recruiter(recruiter_code, collection)
                collection_count = collection.count()

            if st.button("Send") and user_query:
                
                results = collection.query(query_texts=[user_query], n_results = collection_count)
                # st.write(results)


                context = "\n".join(results["documents"][0])
                # st.write(context)
                prompt = f"""
                You are an assistant helping a recruiter with resumes submitted to him and his job postings. Below are the job descriptions and resumes:

                {context}

                Question: {user_query}
                Answer as a helpful assistant and help him select best matching candidates for interviews. 
                Keep the responses consise and in bullet points wherever possible. If the query is out of context, 
                like not any job related or resume related, then just answer out of your general knowledge. 
                """
                model = genai.GenerativeModel("models/gemini-1.5-flash-8b")
                if "gemini_chat" not in st.session_state:
                    st.session_state["gemini_chat"] = model.start_chat(history=[])

                chat = st.session_state["gemini_chat"]
                response = chat.send_message(prompt)


                st.session_state["chat_history"].append({"user": user_query, "ai": response.text})
                with st.container():
                    for chat in st.session_state["chat_history"]:
                        st.write(f"🧑‍🎓: {chat['user']}")
                        st.write(f"🤖: {chat['ai']}")
                        st.markdown("---")

    
    st.markdown("---")
  
    if st.button("Logout"):
        if recruiter_code:
            try:
                recruiter_client.delete_collection(name=f"recruiter_{recruiter_code}")
                print("Recruiter ChromaDB collection deleted successfully.")
            except Exception as e:
                st.error(f"Failed to delete ChromaDB collection: {e}")

        
        st.session_state.pop("chat_history", None)
        st.session_state.pop("gemini_chat", None)

        st.session_state["page"] = "landing"
        st.session_state.pop("recruiter_code", None)
        st.rerun()




# extract text from a PDF
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

# # OCR function
# def ocr_pdf(uploaded_file):
#     pdf_images = []
#     with fitz.open(stream=uploaded_file, filetype="pdf") as pdf:
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

    if "student_name" in st.session_state:
        st.title(f":mortar_board: Welcome, {st.session_state['student_name']}!")
    else:
        st.title(":mortar_board: STUDENT Dashboard")
        st.warning("Please log in to see your details.")
        return 


    student_code = st.session_state.get("student_code")

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

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT pdf_location FROM students WHERE student_code = ?", (student_code,))
    result = cursor.fetchone()
    previous_text = result[0] if result else None

    col1, col2 = st.columns([2, 3])
    with col1:
        st.subheader("Your Resume Text")
        if previous_text:
            st.text_area("Previously Uploaded Resume Text", value=previous_text, height=200, disabled=True)
        else:
            st.info("No resume text found. Please upload your resume.")

        uploaded_file = st.file_uploader("Upload your Resume (PDF only):", type=["pdf"])

        if uploaded_file:
            try:
                
                pdf_text = ""
                with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
                    for page in doc:
                        pdf_text += page.get_text()

                if pdf_text.strip():
                  
                    extracted_skills = []
                    if skills_list:
                        extracted_skills = extract_skills(pdf_text, skills_list)
                    extracted_skills = list(set(extracted_skills))
                    extracted_skills_str = ", ".join(extracted_skills)

                    
                    cursor.execute(
                        "UPDATE students SET pdf_location = ? WHERE student_code = ?",
                        (pdf_text, student_code),
                    )
                    conn.commit()

                   
                    st.markdown("### Extracted Resume Text")
                    st.text_area("Extracted text from your uploaded resume:", value=pdf_text, height=200, disabled=True)

                    st.markdown("### Extracted Skills from Resume")
                    st.write(extracted_skills_str)

                    st.success("Resume text and skills successfully extracted and saved.")
                else:
                    st.error("The uploaded PDF is empty or unreadable.")
            except Exception as e:
                st.error(f"An error occurred while processing the PDF: {str(e)}")

        if job_descriptions:
            st.subheader("Available Job Descriptions from Recruiter")
            jd_options = {jd[1]: f"{jd[1]} - {jd[2][:50]}..." for jd in job_descriptions}  
            selected_jd_title = st.selectbox("Select a Job Description to Apply For", jd_options.keys(), format_func=lambda x: jd_options[x])
        else:
            selected_jd_title = None

   
        col_apply, col_withdraw = st.columns(2)

        with col_apply:
            if st.button("Send Resume to Recruiter"):
                if recruiter_code and previous_text and selected_jd_title:
                   
                    cursor.execute(
                        "SELECT COUNT(*) FROM recruiter_resumes WHERE recruiter_code = ? AND student_code = ? AND jd_title = ?",
                        (recruiter_code, student_code, selected_jd_title),
                    )
                    record_exists = cursor.fetchone()[0]

                    if record_exists:
                        st.warning("You have already sent your resume for this job description.")
                    else:
                        
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
                   
                    cursor.execute(
                        "SELECT COUNT(*) FROM recruiter_resumes WHERE recruiter_code = ? AND student_code = ? AND jd_title = ?",
                        (recruiter_code, student_code, selected_jd_title),
                    )
                    record_exists = cursor.fetchone()[0]

                    if record_exists:
                       
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
            
            if recruiter_exists(recruiter_code):
               
                conn = connect_db()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT title, skills 
                    FROM job_descriptions 
                    JOIN recruiters ON job_descriptions.recruiter_id = recruiters.recruiter_id 
                    WHERE recruiters.recruiter_code = ?
                """, (recruiter_code,))
                job_descriptions = cursor.fetchall()

                
                student_code = st.session_state.get("student_code")
                cursor.execute("SELECT pdf_location FROM students WHERE student_code = ?", (student_code,))
                result = cursor.fetchone()
                conn.close()

                if not result or not result[0]:
                    st.error("No resume uploaded. Please upload your resume first.")
                else:
                    
                    resume_text = result[0]
                    student_skills = extract_skills(resume_text, skills_list)

                    if not student_skills:
                        st.warning("No skills could be extracted from your resume.")
                    else:
                       
                        compatibility_data = []
                        student_embedding = gemini_embedding(", ".join(student_skills)) 
                        for jd_title, jd_skills in job_descriptions:
                            jd_skills_list = jd_skills.split(", ") if jd_skills else []
                            jd_embedding = gemini_embedding(", ".join(jd_skills_list)) 

                            common_skills = set(student_skills).intersection(set(jd_skills_list))
                            compatibility_score = round(len(common_skills) / len(jd_skills_list) * 100, 2) if jd_skills_list else 0
                            abs_compatibility = '✅' if compatibility_score >= 10 else '❌'

                            similarity = cosine_similarity([student_embedding], [jd_embedding])[0][0] * 100

                        
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
    col1, col2 = st.columns([2, 3])

    with col1:
        st.subheader("Contact Recruiter")
        if recruiter_email:
            st.write(f"Compose an email to the recruiter below. Email: {recruiter_email}")
            email_body = st.text_area("Write your email message:", placeholder="Type your message here...", label_visibility='hidden')

            if st.button("Send Email"):
                if email_body.strip():
                    gmail_url = (
                        f"https://mail.google.com/mail/?view=cm&fs=1&to={recruiter_email}"
                        f"&su=Job Inquiry&body={email_body}"
                    )
                    
                    st.markdown(
                        f'<a href="{gmail_url}" target="_blank">Click here to send the email</a>',
                        unsafe_allow_html=True
                    )
                else:
                    st.error("Email body cannot be empty.")

    with col2:
        if "chat_history" not in st.session_state:
            st.session_state["chat_history"] = []

        st.subheader("AI Student Support Chat")
        recruiter_code = recruiter_code
        user_query = st.text_area("Ask a question about resumes or job descriptions:", placeholder="Chat with gemini-1.5-flash-8b")

        embedding_function = GeminiEmbeddingFunction()

        if recruiter_code:
            global client
            client = chromadb.PersistentClient(path="chroma_db")
            collection = client.get_or_create_collection(
                name=f"recruiter_{recruiter_code}",
                embedding_function=embedding_function
            )

            collection_count = collection.count()
            if collection_count == 0:
                st.write("Indexing data for candidate...")
                index_database_data_for_student(recruiter_code, student_code, collection)
                collection_count = collection.count()
                
                
            if st.button("Send") and user_query:
            
                results = collection.query(query_texts=[user_query], n_results = collection_count)


                context = "\n".join(results["documents"][0])
                # st.write(context)
                prompt = f"""
                You are an assistant helping a student with job applications. Below are the job descriptions and resumes:

                {context}

                Question: {user_query}
                Answer as a helpful assistant. Keep the responses consise. If the query is out of context, 
                like not any job related or resume related, then just answer out of your general knowledge.
                """
                model = genai.GenerativeModel("models/gemini-1.5-flash-8b")
                if "gemini_chat" not in st.session_state:
                    st.session_state["gemini_chat"] = model.start_chat(history=[])

                chat = st.session_state["gemini_chat"]
                response = chat.send_message(prompt)


                st.session_state["chat_history"].append({"user": user_query, "ai": response.text})
                with st.container():
                    for chat in st.session_state["chat_history"]:
                        st.write(f"🧑‍🎓: {chat['user']}")
                        st.write(f"🤖: {chat['ai']}")
                        st.markdown("---")

            
  
    st.markdown('---')
    if st.button("Back to Home"):
       
        if recruiter_code:
            try:
                client.delete_collection(name=f"recruiter_{recruiter_code}")
                print("Candidate ChromaDB collection deleted successfully.")
                client.close()
            except Exception as e:
                st.error(f"Failed to delete ChromaDB collection: {e}")

       
        st.session_state.pop("chat_history", None)
        st.session_state.pop("gemini_chat", None)

        
        st.session_state['page'] = 'landing'
        st.rerun()



# def clear_chroma_db():
#     """Function to clear the ChromaDB database."""
#     if os.path.exists('chroma_db') :
#         shutil.rmtree('chroma_db')
#         print("ChromaDB student databases cleared.")
#     if os.path.exists('chroma_db_recruiter'):
#         shutil.rmtree('chroma_db_recruiter')
#         print("ChromaDB recruiter databases cleared.")


# atexit.register(clear_chroma_db)



# Student Login Page
def student_login():
    st.title(":mortar_board: Student Login")

    student_code = st.text_input("Student Code", key="student_code_input")
    password = st.text_input("Password", type="password", key="password_input")

    col1, col2, col3 = st.columns(3)
    

    with col1:
        if st.button("Login"):
            if validate_student(student_code, password):

                conn = connect_db()
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT name FROM students WHERE student_code = ?",
                    (student_code,)
                )
                result = cursor.fetchone()
                conn.close()

                if result:
                    st.session_state['student_name'] = result[0]  
                    st.session_state['student_code'] = student_code
                    st.session_state['page'] = 'student_dashboard'  
                    st.success(f"Welcome, {result[0]}!")
                    st.rerun()
                else:
                    st.error("Error fetching student details. Please contact support.")
            else:
                st.error("Invalid student code or password.")
    

    with col2:
        if st.button("Register as Student"):
            st.session_state['page'] = 'student_registration'
            st.rerun()

    with col3:
        if st.button("Back to Home"):
            st.session_state['page'] = 'landing'
            st.rerun()

# Student Registration Page
def student_registration():
    st.title(":mortar_board: Student Registration")
    
    name = st.text_input("Full Name")
    student_code = st.text_input("Create Student Code")
    password = st.text_input("Create Password", type="password")
    email = st.text_input("Email Address")
    
    if st.button("Register"):
        if name and student_code and password and email:
            if not student_exists(student_code):  
                add_student(student_code, name, password, email)
                st.success("Student registered successfully!")
            else:
                st.error("Student code already exists. Please choose a different code.")
        else:
            st.error("Please fill out all fields.")

    if st.button("Back to Login Page"):
        st.session_state['page'] = 'student_login'
        st.rerun()

# page handling
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
