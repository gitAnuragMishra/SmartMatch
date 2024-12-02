# SmartMatch - Recruitment Assistant

SmartMatch is a recruitment assistant platform designed to streamline hiring processes through intelligent resume parsing, candidate-job matching, and AI-powered chat assistance. It offers dedicated tools for both recruiters and candidates to manage job applications and recruitment efficiently.

---

## Table of Contents

1. [Installation](#installation)
2. [Usage](#usage)
3. [Project Structure](#project-structure)
4. [Features](#features)
5. [Challenges](#challenges)
6. [Technologies](#technologies)
7. [Future Work](#future-work)
8. [License](#license)

---

## Installation

### Prerequisites
- Python 3.8+
- pip


### Install Dependencies

1. Create and activate a virtual environment:
    ```bash
    python -m venv <env-name>
    <env-name>/Scripts/activate

2. Clone the repository:
   ```bash
   git clone https://github.com/gitAnuragMishra/SmartMatch
   cd SmartMatch

3. Install Dependancy:
    ```bash
    pip install -r requirements.txt

4. Create a google gemini API key
    - create an .env file
    - paste the google gemini api key
    ``` 
    GEMINI_API_KEY = <api key>
    
---

### Usage

1. Start the application using Streamlit

    ```bash 
    streamlit run home.py

2. Use the web interface to:
    - Log in/register as a recruiter or student.
    - Upload resumes or job descriptions.
    - View AI-driven matching results and insights.
    - Chat with the AI assistant for recruitment-related queries.
    - Contact the shortlisted candidates or the recruiters.

### Project Structure
```
SmartMatch/
│
├── home.py                 # Main entry point for the Streamlit application
├── database_func.py        # Functions for database interactions
├── chroma_db_func.py       # Functions for indexing and querying using ChromaDB
├── requirements.txt        # Python dependencies
├── extractor_library.json  # skills and education json library
├── jd_pdfs/                # Directory for storing job description PDFs (auto initialisation)
├── chroma_db/              # Directory for ChromaDB persistent storage for candidates (auto initialisation)
├── chroma_db_recruiter/    # Directory for ChromaDB persistent storage for recruiters (auto initialisation)
├── smartmatch.db/          # SQL database for candidate, recruiter details, job descriptions and resumes (auto initialisation)
└── README.md               # ReadMe documentation
```

```
### Features

1. **Recruiter Portal**

    - Job Management: Post and manage job descriptions, including required skills.
    - Resume Review: View candidate profiles and shortlist applicants.
    - Candidate Matching: Score and rank resumes against job descriptions using AI-driven similarity measures.
    - AI Chat Support: Get quick insights into job applications and candidates. Uses Gemini 1.5 Flash-8B with context.
2. **Candidate Portal**
    - Resume Management: Upload and extract skills from resumes.
    - Job Matching: View compatibility scores for job descriptions.
    - AI Chat Support: Get recommendations for job applications. Uses Gemini 1.5 Flash-8B with context.
3. **General Features**
    - Data Persistence: Uses SQLite and ChromaDB for data and embedding storage.
    - PDF Processing: Extract text from resumes and job descriptions.


### Challenges

- Skill Extraction Accuracy: Parsing resumes to accurately extract skills while avoiding irrelevant text.
- Embedding Computation: Generating embeddings and querying large datasets for similarity in real-time.
- Streamlit Session State: Managing user sessions and ensuring smooth navigation within the app.

### Technologies

- **Python**: Core programming language.
- **Streamlit**: Web application framework for building interactive UIs.
- **SQLite**: Database for persistent data storage.
- **ChromaDB**: Database for managing embeddings and similarity queries.
- **HuggingFace Transformers**: For generating text embeddings and sentiment analysis.
- **Google Generative AI**: Model for embeddings and chat assistance.


### Future Work
- **Real-Time Notifications**: Notify recruiters and candidates via email/SMS for key events.
- **Advanced Analytics**: Add dashboards for recruiters with detailed metrics and graphs.
- **Cross-Platform Accessibility**: Develop mobile and desktop apps for wider reach.

### License
This project is licensed under the MIT License. See the LICENSE file for details.