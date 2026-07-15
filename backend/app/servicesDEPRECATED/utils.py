import re
import io
import pdfplumber
from docx import Document

def get_ref_sections(raw_text):
    # Normalize text to single line for easier regex
    text_norm = " ".join(raw_text.split())

    s1_pat = r"1\.\s*Summary of the impact(.*?)(?=2\.\s*Underpinning research)"
    s2_pat = r"2\.\s*Underpinning research(.*?)(?=3\.\s*References to the research)"
    s4_pat = r"4\.\s*Details of the impact(.*?)(?=5\.\s*Sources to corroborate|$)"

    s1_match = re.search(s1_pat, text_norm, re.IGNORECASE)
    s2_match = re.search(s2_pat, text_norm, re.IGNORECASE)
    s4_match = re.search(s4_pat, text_norm, re.IGNORECASE)

    summary = s1_match.group(1).strip() if s1_match else ""
    underpinning = s2_match.group(1).strip() if s2_match else ""
    details = s4_match.group(1).strip() if s4_match else ""

    # --- THE FIX: If slicing fails, don't return empty strings ---
    if not summary or not details:
        print("WARNING: Slicing failed. Falling back to full text.")
        return {
            "feature_text": raw_text,
            "embedding_text": raw_text
        }

    return {
        "feature_text": f"{summary} {details}",
        "embedding_text": f"{summary}\n{underpinning}\n{details}"
    }

def clean_boilerplate(text):
    boilerplate_patterns = [
        r"Impact case study \(REF3b\)",
        r"REF2014",
        r"Research Excellence Framework",
        r"Page \d+",
    ]

    clean_text = text
    for pattern in boilerplate_patterns:
        clean_text = re.sub(pattern, "", clean_text, flags=re.IGNORECASE)
    
    return clean_text.strip()

def convert_bytes_to_text(file_bytes, ext):
    text = ""

    try:
        if ext == "pdf":
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                pages = [page.extract_text() for page in pdf.pages if page.extract_text()]
                text = "\n".join(pages)
        elif ext in ["docx", "doc"]:
            doc = Document(io.BytesIO(file_bytes))
            text = "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        print(f"Error processing file: {e}")
        return ""

    return text