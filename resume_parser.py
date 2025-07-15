import re
import sys
import json
import os
import pdfplumber
import spacy

try:
    from fuzzywuzzy import fuzz
except ImportError:
    fuzz = None  # Will use fallback method

# Load spaCy English model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Downloading 'en_core_web_sm' model...")
    from spacy.cli import download
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

# ---------- Text Extraction ----------
def extract_text_from_pdf(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

# ---------- Contact Info ----------
def extract_email(text):
    matches = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    return matches[0] if matches else None

def extract_phone_number(text):
    phone_pattern = r'(\+?\d{1,3}[-.\s]?)?(\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}'
    match = re.search(phone_pattern, text)
    return match.group() if match else None

# ---------- Name Extraction ----------
def extract_name(text):
    doc = nlp(text)
    lines = text.strip().split('\n')
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            if ent.text in lines[0] or ent.text in lines[1]:  # Likely near top
                return ent.text
    return None

# ---------- Education Extraction ----------
def extract_education(text):
    degrees = ['B.Tech', 'M.Tech', 'B.E', 'M.E', 'B.Sc', 'M.Sc', 'PhD', 'MBA', 'BCA', 'MCA']
    education = []
    for line in text.split('\n'):
        if any(degree.lower() in line.lower() for degree in degrees):
            education.append(line.strip())
    return list(set(education)) if education else None

# ---------- Skills Extraction ----------
def extract_skills(text):
    base_skills = [
        "python", "java", "c++", "machine learning", "data analysis", "sql",
        "aws", "docker", "javascript", "react", "node.js", "deep learning",
        "nlp", "tensorflow", "pandas", "numpy", "html", "css", "flask", "django"
    ]
    text_lower = text.lower()
    found_skills = set()

    if fuzz:
        for skill in base_skills:
            if fuzz.partial_ratio(skill.lower(), text_lower) > 80:
                found_skills.add(skill)
    else:
        found_skills = {skill for skill in base_skills if skill in text_lower}

    return sorted(list(found_skills)) if found_skills else None

# ---------- Resume Parser ----------
def parse_resume(file_path):
    print(f"\n📄 Parsing resume: {file_path}")
    if not os.path.isfile(file_path):
        raise FileNotFoundError("File does not exist")

    if not file_path.lower().endswith(".pdf"):
        raise ValueError("Only PDF resumes are supported")

    text = extract_text_from_pdf(file_path)

    data = {
        "name": extract_name(text),
        "email": extract_email(text),
        "phone": extract_phone_number(text),
        "education": extract_education(text),
        "skills": extract_skills(text)
    }

    return data

# ---------- Main ----------
def main():
    if len(sys.argv) != 2:
        print("Usage: python enhanced_resume_parser.py your_resume.pdf")
        sys.exit(1)

    resume_path = sys.argv[1]

    try:
        parsed_data = parse_resume(resume_path)
        print("\n✅ Parsed Resume Data:")
        print(json.dumps(parsed_data, indent=2))

        # Save result to JSON file
        output_file = "parsed_resume_output.json"
        with open(output_file, "w") as f:
            json.dump(parsed_data, f, indent=2)
        print(f"\n📁 Output saved to: {output_file}")

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")

if __name__ == "__main__":
    main()
