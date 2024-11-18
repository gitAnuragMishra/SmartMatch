import streamlit as st
import pdfplumber  # PyMuPDF
from io import BytesIO
import pytesseract
from PIL import Image
import sqlite3

from database_func import add_recruiter, validate_recruiter, recruiter_exists, get_job_descriptions, save_job_description, delete_all_job_descriptions, student_exists, add_student, validate_student, connect_db#, delete_job_description  # Import functions from the database module

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
        if previous_descriptions:
            selected_title = st.selectbox(
                "Select a previously uploaded job description by title",
                options=list(previous_descriptions.keys()),
                key="description_select"
            )
            if selected_title:
                with st.expander(f"**View Job Description: {selected_title}**", expanded=False):
                    st.write(previous_descriptions[selected_title])  # Display the full description inside the expander

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
                    st.write(job_description)
                else:
                    st.error("Could not extract text. Ensure the PDF contains selectable text or use an OCR-enabled PDF.")

        # Save Job Description Button
        if job_title and job_description and st.button("Save Job Description", key="save_button"):
            if save_job_description(recruiter_code, job_title, job_description):
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
        st.subheader("Schedule Interviews")
        st.write("Seamlessly schedule interviews using Google Meet and Calendar integration.")

    with col3:
        st.subheader("Review Resumes")
        st.write("View candidate profiles and review their skills and experience.")

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
        with pdfplumber.open(BytesIO(uploaded_file.read())) as pdf:
            for page in pdf.pages:
                pdf_text += page.extract_text() or ""

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

    recruiter_code = st.text_input("Enter Recruiter Code to Connect")
    recruiter_email = None

    if recruiter_code:
        if recruiter_exists(recruiter_code):
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("SELECT email FROM recruiters WHERE recruiter_code = ?", (recruiter_code,))
            result = cursor.fetchone()
            conn.close()

            if result:
                recruiter_email = result[0]
                st.success(f"Recruiter found. ")
            else:
                st.error("Recruiter email not found.")
        else:
            st.error("Invalid recruiter code.")
    
    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Score your Resume")
        st.write("Upload your resume and score your skills and experience to get matched with recruiters.")
    with col2:
        st.subheader("Contact Recruiter")
        if recruiter_email:
            st.write(f"Compose an email to the recruiter below. Email: {recruiter_email}")
            email_body = st.text_area("Write your email message:", placeholder='Type your message here...', label_visibility='hidden')

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
