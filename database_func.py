import sqlite3
import streamlit as st
import os
import atexit
import shutil
import re


def connect_db():
    conn = sqlite3.connect("smartmatch.db")
    return conn


def create_tables():
    conn = connect_db()
    c = conn.cursor()

    # Create recruiters table
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS recruiters (
            recruiter_id INTEGER PRIMARY KEY AUTOINCREMENT ,
            recruiter_code TEXT UNIQUE,
            password TEXT,
            email TEXT UNIQUE NOT NULL
        )
        """
    )

    # Create job_descriptions table with title
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS job_descriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recruiter_id INTEGER,
            title TEXT,
            description TEXT, 
            jd_pdf_location TEXT DEFAULT NULL,
            skills TEXT DEFAULT NULL,
            FOREIGN KEY (recruiter_id) REFERENCES recruiters (recruiter_id)
        )
        """
    )
    # Create students table
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS students (
            student_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_code TEXT UNIQUE,
            name TEXT NOT NULL,
            password TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            pdf_location TEXT DEFAULT NULL
        )
        """
    )
    # Create resumes table
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS recruiter_resumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recruiter_code TEXT NOT NULL,
            student_code TEXT NOT NULL,
            resume_text TEXT NOT NULL,
            jd_title TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            extracted_resume_skills TEXT DEFAULT NULL,
            FOREIGN KEY (recruiter_code) REFERENCES recruiters(recruiter_code),
            FOREIGN KEY (student_code) REFERENCES students(student_code)
        )

        """
    )
    conn.commit()
    conn.close()


def add_recruiter(recruiter_code, password, email):
    conn = connect_db()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO recruiters (recruiter_code, password, email) VALUES (?, ?, ?)", (recruiter_code, password, email))
        conn.commit()
        st.success("Recruiter account created successfully!")
    except sqlite3.IntegrityError:
        st.error("Recruiter code already exists. Please choose a unique code.")
    finally:
        conn.close()


def validate_recruiter(recruiter_code, password):
    conn = connect_db()
    c = conn.cursor()
    c.execute("SELECT * FROM recruiters WHERE recruiter_code = ? AND password = ?", (recruiter_code, password))
    result = c.fetchone()
    conn.close()
    return result is not None


def recruiter_exists(recruiter_code):
    conn = connect_db()
    c = conn.cursor()
    c.execute("SELECT * FROM recruiters WHERE recruiter_code = ?", (recruiter_code,))
    exists = c.fetchone() is not None
    conn.close()
    return exists

# Student Functions
def add_student(student_code, name, password, email):
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO students (student_code, name, password, email) VALUES (?, ?, ?, ?)",
            (student_code, name, password, email),
        )
        conn.commit()
        st.success("Student account created successfully!")
    except sqlite3.IntegrityError as e:
        st.error(f"Error: {e}")
    finally:
        conn.close()

def validate_student(student_code, password):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM students WHERE student_code = ? AND password = ?",
        (student_code, password),
    )
    result = cursor.fetchone()
    conn.close()
    return result is not None



def student_exists(student_code):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students WHERE student_code = ?", (student_code,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists


def extract_skills(text, skills_list):
    skills = []

    for skill in skills_list:
        pattern = r"\b{}\b".format(re.escape(skill))
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            skills.append(skill)

    return skills

def save_job_description(recruiter_code, title, job_description, jd_pdf_file=None, skills_list=None):
    conn = connect_db()
    c = conn.cursor()
    try:
        # Fetch recruiter ID
        c.execute("SELECT recruiter_id FROM recruiters WHERE recruiter_code = ?", (recruiter_code,))
        recruiter = c.fetchone()
        if recruiter:
            recruiter_id = recruiter[0]
            pdf_location = None
            
            # Save uploaded PDF
            if jd_pdf_file:
                pdf_dir = "jd_pdfs"
                os.makedirs(pdf_dir, exist_ok=True)
                sanitized_title = re.sub(r'[^\w\-_\. ]', '_', title)
                pdf_file_path = os.path.join(pdf_dir, f"{sanitized_title}_{recruiter_id}.pdf")
                with open(pdf_file_path, "wb") as f:
                    f.write(jd_pdf_file.getbuffer())
                pdf_location = pdf_file_path

            # Extract skills
            extracted_skills = []
            if skills_list:
                extracted_skills = extract_skills(job_description, skills_list)
            extracted_skills = list(set(extracted_skills))
            skills_str = ", ".join(extracted_skills)  # Convert skills list to comma-separated string

            # Insert job description with skills
            c.execute(
                "INSERT INTO job_descriptions (recruiter_id, title, description, jd_pdf_location, skills) VALUES (?, ?, ?, ?, ?)",
                (recruiter_id, title, job_description, pdf_location, skills_str),
            )
            conn.commit()
            return True
        else:
            st.error("Recruiter not found.")
            return False
    except Exception as e:
        st.error(f"Error saving job description: {e}")
        return False
    finally:
        conn.close()



def get_job_descriptions(recruiter_code):
    conn = connect_db()
    c = conn.cursor()
    try:
        c.execute("SELECT recruiter_id FROM recruiters WHERE recruiter_code = ?", (recruiter_code,))
        recruiter = c.fetchone()
        if recruiter:
            recruiter_id = recruiter[0]
            # Fetch title and description
            c.execute("SELECT title, description FROM job_descriptions WHERE recruiter_id = ?", (recruiter_id,))
            descriptions = c.fetchall()
            # Map titles to descriptions
            return {desc[0]: desc[1] for desc in descriptions}
        else:
            return {}
    except Exception as e:
        st.error(f"Error fetching job descriptions: {e}")
        return {}
    finally:
        conn.close()


# def delete_job_description(description_id):
#     conn = connect_db()
#     c = conn.cursor()
#     try:
#         c.execute("DELETE FROM job_descriptions WHERE id = ?", (description_id,))
#         conn.commit()
#         return True
#     except Exception as e:
#         st.error(f"Error deleting job description: {e}")
#         return False
#     finally:
#         conn.close()

def delete_all_job_descriptions(recruiter_code):
    conn = connect_db()
    c = conn.cursor()
    try:
        # Fetch recruiter_id by recruiter_code
        c.execute("SELECT recruiter_id FROM recruiters WHERE recruiter_code = ?", (recruiter_code,))
        recruiter = c.fetchone()
        if recruiter:
            recruiter_id = recruiter[0]
            # Delete all job descriptions for the recruiter
            c.execute("DELETE FROM job_descriptions WHERE recruiter_id = ?", (recruiter_id,))
            conn.commit()
            return True
        else:
            st.error("Recruiter not found.")
            return False
    except Exception as e:
        st.error(f"Error deleting job descriptions: {e}")
        return False
    finally:
        conn.close()

def unlink_database():
    """Delete the database file when the application closes."""
    db_path = "smartmatch.db"
    if os.path.exists(db_path):
        try:
            os.unlink(db_path)
            print(f"Database {db_path} has been deleted successfully.")
        except Exception as e:
            print(f"Error unlinking the database: {e}")
# atexit.register(unlink_database)



# Ensure tables are created at runtime
create_tables()
