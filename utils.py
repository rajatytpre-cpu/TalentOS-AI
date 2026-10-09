import pandas as pd
import re

SKILL_LIBRARY = [
 "python","sql","excel","power bi","tableau","data analysis","dashboarding",
 "communication","stakeholder management","problem solving","project management",
 "marketing","sales","financial analysis","forecasting","machine learning",
 "customer research","recruitment","talent acquisition","workforce planning",
 "negotiation","leadership","people analytics","business analysis","presentation",
 "crm","statistics","risk analysis","supply chain","inventory optimization"
]

def parse_skills(text):
    t=str(text).lower()
    return [s for s in SKILL_LIBRARY if re.search(r"(?<!\w)"+re.escape(s)+r"(?!\w)",t)]

def load_demo_candidates():
    rows=[
      ["T-001","Aarav Mehta","Business Analyst Intern",1,"New","Delhi NCR","Built Excel dashboards, used SQL queries for data cleaning, Power BI reporting, stakeholder communication and business analysis. Presented insights to project teams."],
      ["T-002","Meera Kapoor","Marketing Associate",2,"Screening","Gurugram","Marketing campaign analysis, Excel, customer research, communication, presentation, dashboarding and stakeholder management. Worked with CRM reports."],
      ["T-003","Kabir Shah","Data Analyst",3,"Interview","Bengaluru","Python, SQL, Excel, Power BI, statistics, machine learning and data analysis. Created automated reporting and dashboards for business teams."],
      ["T-004","Ananya Rao","HR Coordinator",2,"Screening","Mumbai","Recruitment coordination, talent acquisition, communication, stakeholder management, Excel reporting and project management."],
      ["T-005","Vihaan Sethi","Sales Executive",4,"New","Pune","Sales, negotiation, CRM, customer relationships, forecasting, communication and account management. Tracked pipeline and quarterly targets."],
      ["T-006","Sara Iyer","Operations Analyst",3,"Interview","Hyderabad","Supply chain, inventory optimization, Excel, SQL, forecasting, problem solving and process improvement. Created operational performance dashboards."]
    ]
    return pd.DataFrame(rows,columns=["Candidate_ID","Name","Current_Role","Experience_Years","Stage","Location","Resume_Text"])

def extract_uploaded_text(uploaded_file):
    """Extract text from uploaded PDF, DOCX, or TXT files."""
    from io import BytesIO

    filename = uploaded_file.name.lower()
    content = uploaded_file.getvalue()

    if filename.endswith(".pdf"):
        from pypdf import PdfReader
        reader = PdfReader(BytesIO(content))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)

    elif filename.endswith(".docx"):
        from docx import Document
        document = Document(BytesIO(content))
        text = "\n".join(p.text for p in document.paragraphs)

    elif filename.endswith(".txt"):
        text = content.decode("utf-8", errors="replace")

    else:
        raise ValueError("Upload a PDF, DOCX, or TXT file.")

    if not text.strip():
        raise ValueError("No readable text found. Scanned PDFs need OCR.")

    return text.strip()
