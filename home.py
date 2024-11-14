import streamlit as st
import pdfplumber  # PyMuPDF
from io import BytesIO
import pytesseract
from PIL import Image

from database_func import add_recruiter, validate_recruiter, recruiter_exists, get_job_descriptions, save_job_description  # Import functions from the database module

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
    with col2:
        if st.button("STUDENT"):
            st.session_state['page'] = 'student'
            st.rerun()

# Recruiter Login Page
def recruiter_login():
    st.title(":office_worker: Recruiter Login")
    recruiter_code = st.text_input("Recruiter Code")
    password = st.text_input("Password", type="password")
    
    # Login and Registration Buttons
    col1, col2 = st.columns(2)
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

# Recruiter Registration Page
def recruiter_registration():
    st.title("Recruiter Registration")
    new_recruiter_code = st.text_input("Create Recruiter Code")
    new_password = st.text_input("Create Password", type="password")
    
    if st.button("Register"):
        if new_recruiter_code and new_password:
            add_recruiter(new_recruiter_code, new_password)
            st.success("Recruiter registered successfully!")
        else:
            st.error("Please enter both code and password.")
    
    # Back to Login Page button
    if st.button("Back to Login Page"):
        st.session_state['page'] = 'recruiter_login'
        st.rerun()

# Recruiter Dashboard
def recruiter_dashboard():
    st.title(":office_worker: RECRUITER Dashboard")
    st.write(f"Welcome, Recruiter! Manage candidates, review profiles, and match with ideal candidates.")
    st.markdown("---")

    # Job Openings Section with Save Feature
    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("Job Openings")
        st.write("Post job openings, filter based on qualifications, and manage each candidate's status in the hiring pipeline.")

        # Fetch previously uploaded job descriptions
        recruiter_code = st.session_state['recruiter_code']
        previous_descriptions = get_job_descriptions(recruiter_code)

        # Dropdown for previously uploaded job descriptions
        if previous_descriptions:
            selected_description = st.selectbox("Select a previously uploaded job description", options=previous_descriptions.keys())
            if selected_description:
                st.write("**Selected Job Description:**")
                st.write(previous_descriptions[selected_description])

        # Option to paste or upload job description
        job_description_option = st.radio(
            "How would you like to add the job description?",
            ("Paste text", "Upload PDF")
        )

        if job_description_option == "Paste text":
            job_description = st.text_area("Paste job description here")
        elif job_description_option == "Upload PDF":
            uploaded_file = st.file_uploader("Upload job description PDF", type="pdf")
            job_description = ""
            if uploaded_file is not None:
                job_description = extract_text_from_pdf(uploaded_file)
                if job_description:
                    st.write("**Extracted Job Description:**")
                    st.write(job_description)
                else:
                    st.error("Could not extract text. Please ensure the PDF contains selectable text or use an OCR-enabled PDF.")

        # Save Job Description Button
        if job_description and st.button("Save Job Description"):
            if save_job_description(recruiter_code, job_description):
                st.success("Job description saved successfully!")
            else:
                st.error("Failed to save job description.")

    # Remaining sections
    with col2:
        st.subheader("Schedule Interviews")
        st.write("Seamlessly schedule interviews using Google Meet and Calendar integration.")
    with col3:
        st.subheader("Review Resumes")
        st.write("View candidate profiles and review their skills and experience.")
    
    st.markdown("---")

    # Logout button
    if st.button("Logout"):
        st.session_state['page'] = 'landing'
        st.session_state.pop('recruiter_code', None)
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
def student_page():
    st.title(":mortar_board: STUDENT Dashboard")
    recruiter_code = st.text_input("Enter Recruiter Code to Connect")
    
    if recruiter_code:
        if recruiter_exists(recruiter_code):
            st.success("Recruiter found. You can proceed with profile actions.")
        else:
            st.error("Invalid recruiter code.")
    
    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Score your Resume")
        st.write("Upload your resume and score your skills and experience to get matched with recruiters.")
    with col2:
        st.subheader("Contact Recruiter")
        st.write("Connect with recruiters for interviews, feedback, and more.")
    
    st.markdown("---")
    
    # Back to Home button
    if st.button("Back to Home"):
        st.session_state['page'] = 'landing'
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
elif st.session_state['page'] == 'student':
    student_page()
