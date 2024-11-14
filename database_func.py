import sqlite3
import streamlit as st

# Database connection
def connect_db():
    conn = sqlite3.connect('smartmatch.db')
    return conn

# Create tables for recruiter credentials if not already exist
def create_tables():
    conn = connect_db()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS recruiters (
            recruiter_id INTEGER PRIMARY KEY AUTOINCREMENT,
            recruiter_code TEXT UNIQUE,
            password TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Function to add a recruiter
def add_recruiter(recruiter_code, password):
    conn = connect_db()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO recruiters (recruiter_code, password) VALUES (?, ?)", (recruiter_code, password))
        conn.commit()
        st.success("Recruiter account created successfully!")
    except sqlite3.IntegrityError:
        st.error("Recruiter code already exists. Please choose a unique code.")
    conn.close()

# Function to validate recruiter login
def validate_recruiter(recruiter_code, password):
    conn = connect_db()
    c = conn.cursor()
    c.execute("SELECT * FROM recruiters WHERE recruiter_code = ? AND password = ?", (recruiter_code, password))
    result = c.fetchone()
    conn.close()
    return result is not None

# Function to check if recruiter code exists (for students)
def recruiter_exists(recruiter_code):
    conn = connect_db()
    c = conn.cursor()
    c.execute("SELECT * FROM recruiters WHERE recruiter_code = ?", (recruiter_code,))
    exists = c.fetchone() is not None
    conn.close()
    return exists

# Run the initial table creation
create_tables()


def save_job_description(recruiter_code, job_description):
    # Insert code to save job_description in database, tied to recruiter_code
    pass

def get_job_descriptions(recruiter_code):
    # Fetch saved job descriptions for the given recruiter_code
    # Return as a dictionary where keys are descriptions titles, values are descriptions
    pass