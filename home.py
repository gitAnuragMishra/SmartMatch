import streamlit as st

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
            st.session_state['page'] = 'recruiter'
            st.rerun()
    with col2:
        if st.button("STUDENT"):
            st.session_state['page'] = 'student'
            st.rerun()

# Recruiter Page
def recruiter_page():
    st.title(":office_worker: RECRUITER Dashboard")
    st.write("Welcome to the Recruiter Dashboard! Here, you can post job openings, review student profiles, and match with ideal candidates.")
    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Manage Candidates")
        st.write("Post job openings, filter based on qualifications, and manage each candidate's status in the hiring pipeline.")
    with col2:
        st.subheader("Schedule Interviews")
        st.write("Seamlessly schedule interviews using google meet and calender integration.")
    
    st.markdown("---")
    
    # Back to Home button
    if st.button("Back to Home"):
        st.session_state['page'] = 'landing'
        st.rerun()

# Student Page
def student_page():
    st.title(":mortar_board: STUDENT Dashboard")
    st.write("Welcome to the Student Dashboard! Create your profile, view job opportunities, and get matched with top recruiters.")
    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Score your resume")
        st.write("Upload your resume and score your skills and experience to get matched with recruiters.")
    with col2:
        st.subheader("Contact Recuiter")
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
elif st.session_state['page'] == 'recruiter':
    recruiter_page()
elif st.session_state['page'] == 'student':
    student_page()
