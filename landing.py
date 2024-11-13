import streamlit as st

# Page config
st.set_page_config(page_title="SmartMatch", page_icon=":briefcase:", layout="wide")

# Sidebar
with st.sidebar:
    st.title("SmartMatch :briefcase:")
    st.write("AI-Powered Recruitment Assistant")
    st.markdown("---")
    st.header("Navigation")
    nav_option = st.radio("Go to", ["Dashboard", "Upload CVs", "Job Matching", "Candidate Outreach", "Interview Scheduling", "Feedback"])

# Main Page
st.title(":briefcase: SmartMatch - Recruitment Assistant")
st.write("Welcome to SmartMatch! This platform streamlines the recruitment process, from resume parsing to candidate matching and interview scheduling.")

# Function to display each section based on selected option
def display_dashboard():
    st.subheader("Dashboard")
    st.write("An overview of the recruitment process, including current job openings, candidate status, and performance metrics.")
    st.metric("Candidates Processed", "150")
    st.metric("Matches Found", "45")
    st.metric("Interviews Scheduled", "25")

def display_upload_cvs():
    st.subheader("Upload CVs")
    st.write("Upload resumes to start sourcing candidates.")
    uploaded_files = st.file_uploader("Choose CV files to upload", type=["pdf", "docx"], accept_multiple_files=True)
    if uploaded_files:
        st.success(f"{len(uploaded_files)} CV(s) uploaded successfully!")
    st.button("Process Resumes")

def display_job_matching():
    st.subheader("Job Matching")
    st.write("Match candidates to specific job openings based on their skills and experience.")
    job_title = st.selectbox("Select Job Opening", ["Software Engineer", "Data Analyst", "Product Manager"])
    st.write(f"Selected job: {job_title}")
    st.button("Find Matches")
    st.write("List of matched candidates will appear here...")

def display_candidate_outreach():
    st.subheader("Candidate Outreach")
    st.write("Send personalized messages to shortlisted candidates.")
    candidate_name = st.selectbox("Select Candidate", ["John Doe", "Jane Smith", "Chris Johnson"])
    st.write(f"Selected candidate: {candidate_name}")
    message = st.text_area("Message to Candidate", "Hello [Candidate], we’d like to invite you to the next steps of the hiring process.")
    st.button("Send Message")

def display_interview_scheduling():
    st.subheader("Interview Scheduling")
    st.write("Book interviews with candidates.")
    candidate_name = st.selectbox("Select Candidate", ["John Doe", "Jane Smith", "Chris Johnson"])
    interview_time = st.date_input("Choose Interview Date")
    interview_slot = st.time_input("Choose Interview Time")
    st.button("Schedule Interview")

def display_feedback():
    st.subheader("Feedback")
    st.write("Gather and review feedback on candidates.")
    candidate_name = st.selectbox("Select Candidate", ["John Doe", "Jane Smith", "Chris Johnson"])
    feedback = st.text_area("Feedback", "Enter feedback on candidate's interview performance.")
    st.button("Submit Feedback")

# Display the appropriate section based on the user's selection
if nav_option == "Dashboard":
    display_dashboard()
elif nav_option == "Upload CVs":
    display_upload_cvs()
elif nav_option == "Job Matching":
    display_job_matching()
elif nav_option == "Candidate Outreach":
    display_candidate_outreach()
elif nav_option == "Interview Scheduling":
    display_interview_scheduling()
elif nav_option == "Feedback":
    display_feedback()

# Footer
st.sidebar.markdown("---")
st.sidebar.write("SmartMatch - Powered by AI")
