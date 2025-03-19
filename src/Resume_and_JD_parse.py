import os
import json
import PyPDF2
import spacy
import nltk
from datetime import datetime
from pathlib import Path

# Download required NLTK data
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
nltk.download('maxent_ne_chunker')
nltk.download('words')

# Load spaCy model
nlp = spacy.load('en_core_web_sm')

class DocumentParser:
    def __init__(self):
        self.saved_details_path = Path("saved_details")
        self.saved_details_path.mkdir(exist_ok=True)

    def extract_text_from_pdf(self, pdf_path):
        """Extract text from PDF file."""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text()
                return text.strip()
        except Exception as e:
            print(f"Error reading PDF file: {e}")
            return None

    def parse_resume(self, text):
        """Parse resume text into structured data."""
        doc = nlp(text)
        
        # Initialize resume sections
        resume_data = {
            "personal_info": {},
            "education": [],
            "experience": [],
            "skills": [],
            "raw_text": text
        }

        # Extract entities using spaCy
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                resume_data["personal_info"]["name"] = ent.text
            elif ent.label_ == "EMAIL":
                resume_data["personal_info"]["email"] = ent.text
            elif ent.label_ == "GPE":  # Geographical location
                resume_data["personal_info"].setdefault("location", []).append(ent.text)

        # Extract skills (simple approach - can be enhanced)
        skills = []
        for token in doc:
            if token.pos_ in ["NOUN", "PROPN"] and len(token.text) > 2:
                skills.append(token.text)
        resume_data["skills"] = list(set(skills))  # Remove duplicates

        return resume_data

    def parse_job_description(self, text):
        """Parse job description text into structured data."""
        doc = nlp(text)
        
        jd_data = {
            "title": "",
            "company": "",
            "requirements": [],
            "responsibilities": [],
            "qualifications": [],
            "raw_text": text
        }

        # Simple section identification (can be enhanced)
        current_section = None
        for sent in doc.sents:
            sent_text = sent.text.lower()
            if "requirements" in sent_text or "qualifications" in sent_text:
                current_section = "requirements"
                jd_data["requirements"].append(sent.text)
            elif "responsibilities" in sent_text or "duties" in sent_text:
                current_section = "responsibilities"
                jd_data["responsibilities"].append(sent.text)
            elif current_section:
                jd_data[current_section].append(sent.text)

        return jd_data

    def save_as_json(self, data, file_type):
        """Save parsed data as JSON file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{file_type}_{timestamp}.json"
        filepath = self.saved_details_path / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        
        print(f"Saved {file_type} data to {filepath}")
        return filepath

    def process_documents(self, resume_path, jd_path):
        """Process both resume and job description documents."""
        # Process Resume
        resume_text = self.extract_text_from_pdf(resume_path)
        if resume_text:
            resume_data = self.parse_resume(resume_text)
            self.save_as_json(resume_data, "resume")
        else:
            print("Failed to process resume")

        # Process Job Description
        jd_text = self.extract_text_from_pdf(jd_path)
        if jd_text:
            jd_data = self.parse_job_description(jd_text)
            self.save_as_json(jd_data, "job_description")
        else:
            print("Failed to process job description")

def main():
    parser = DocumentParser()
    
    # Get file paths from user
    resume_path = input("Enter the path to your resume PDF: ")
    jd_path = input("Enter the path to the job description PDF: ")
    
    # Process the documents
    parser.process_documents(resume_path, jd_path)

if __name__ == "__main__":
    main()