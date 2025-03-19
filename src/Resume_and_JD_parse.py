import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain.chains import LLMChain
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv()

# Define output schemas using Pydantic
class PersonalInfo(BaseModel):
    name: str = Field(description="Full name of the person")
    email: Optional[str] = Field(description="Email address", default=None)
    phone: Optional[str] = Field(description="Phone number", default=None)
    location: Optional[str] = Field(description="Current location", default=None)
    linkedin: Optional[str] = Field(description="LinkedIn profile URL", default=None)

class Education(BaseModel):
    degree: str = Field(description="Degree name")
    institution: Optional[str] = Field(description="Institution name", default="Not specified")
    graduation_year: Optional[str] = Field(description="Year of graduation", default=None)
    gpa: Optional[str] = Field(description="GPA if mentioned", default=None)
    major: Optional[str] = Field(description="Field of study/Major", default=None)

class Experience(BaseModel):
    company: str = Field(description="Company name")
    position: str = Field(description="Job title/position")
    duration: Optional[str] = Field(description="Duration of employment", default="Not specified")
    description: List[str] = Field(description="List of responsibilities and achievements", default_factory=list)

class Project(BaseModel):
    name: str = Field(description="Name of the project")
    duration: Optional[str] = Field(description="Duration or timeframe of the project", default=None)
    description: str = Field(description="Detailed description of the project")
    technologies: List[str] = Field(description="Technologies, tools, and languages used", default_factory=list)
    role: Optional[str] = Field(description="Role in the project", default=None)
    url: Optional[str] = Field(description="Project URL or repository link if available", default=None)
    achievements: Optional[List[str]] = Field(description="Key achievements or outcomes of the project", default_factory=list)

class ResumeData(BaseModel):
    personal_info: PersonalInfo = Field(description="Personal information of the candidate")
    education: List[Education] = Field(description="List of educational qualifications", default_factory=list)
    experience: List[Experience] = Field(description="List of work experiences", default_factory=list)
    projects: List[Project] = Field(description="List of projects worked on", default_factory=list)
    skills: List[str] = Field(description="List of technical and soft skills", default_factory=list)

class JobDescription(BaseModel):
    title: str = Field(description="Job title")
    company: str = Field(description="Company name")
    location: Optional[str] = Field(description="Job location", default=None)
    requirements: List[str] = Field(description="List of job requirements", default_factory=list)
    responsibilities: List[str] = Field(description="List of job responsibilities", default_factory=list)
    qualifications: List[str] = Field(description="List of required qualifications", default_factory=list)
    preferred_skills: List[str] = Field(description="List of preferred skills", default_factory=list)

class DocumentParser:
    def __init__(self):
        self.saved_details_path = Path("saved_details")
        self.saved_details_path.mkdir(exist_ok=True)
        
        # Initialize LangChain components
        self.llm = ChatOpenAI(
            model_name="gpt-4-turbo-preview",
            temperature=0,
        )
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,
            chunk_overlap=200,
            length_function=len,
        )

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF file."""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text()
                return text.strip()
        except Exception as e:
            print(f"Error reading PDF file: {e}")
            return None

    def merge_resume_data(self, data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge multiple resume data dictionaries into one."""
        if not data_list:
            return None

        # Initialize with the first chunk's data
        merged_data = data_list[0]

        # Merge data from subsequent chunks
        for data in data_list[1:]:
            if not data:
                continue
            
            # Merge education entries
            merged_data['education'].extend(data.get('education', []))
            
            # Merge experience entries
            merged_data['experience'].extend(data.get('experience', []))
            
            # Merge projects
            merged_data['projects'].extend(data.get('projects', []))
            
            # Merge skills (remove duplicates)
            all_skills = set(merged_data['skills'])
            all_skills.update(data.get('skills', []))
            merged_data['skills'] = list(all_skills)

        # Remove duplicate entries based on name/title
        merged_data['education'] = self._remove_duplicates(merged_data['education'], 'degree')
        merged_data['experience'] = self._remove_duplicates(merged_data['experience'], 'position')
        merged_data['projects'] = self._remove_duplicates(merged_data['projects'], 'name')

        return merged_data

    def _remove_duplicates(self, items: List[Dict], key_field: str) -> List[Dict]:
        """Remove duplicate entries based on a key field."""
        seen = set()
        unique_items = []
        
        for item in items:
            item_key = item.get(key_field, '')
            if item_key and item_key not in seen:
                seen.add(item_key)
                unique_items.append(item)
        
        return unique_items

    def parse_resume(self, text: str) -> Dict[str, Any]:
        """Parse resume text using LangChain and OpenAI."""
        # Create output parser
        parser = PydanticOutputParser(pydantic_object=ResumeData)

        # Create prompt template
        resume_template = """
        Extract structured information from the following resume text. 
        Pay special attention to projects section and include all project details in the specified format.
        Make sure to extract all relevant information about projects including technologies used and achievements.
        If any field is not found in the text, use appropriate default values (empty list for lists, "Not specified" for optional strings, or null).
        
        For education entries, if institution is not clearly mentioned, use "Not specified" instead of null.
        For experience entries, ensure company and position are provided, use "Not specified" for missing duration.
        For projects, ensure name and description are always provided, use empty lists for missing technologies and achievements.

        Important: Extract ALL projects mentioned in the text, don't skip any projects even if they seem less significant.

        Resume Text:
        {text}

        {format_instructions}
        """

        prompt = PromptTemplate(
            template=resume_template,
            input_variables=["text"],
            partial_variables={"format_instructions": parser.get_format_instructions()}
        )

        # Create chain
        chain = LLMChain(llm=self.llm, prompt=prompt)

        # Split text and process all chunks
        texts = self.text_splitter.split_text(text)
        parsed_chunks = []
        
        for chunk in texts:
            try:
                result = chain.run(text=chunk)
                parsed_data = parser.parse(result)
                parsed_chunks.append(parsed_data.model_dump())
            except Exception as e:
                print(f"Error parsing chunk: {e}")
                continue

        # Merge results from all chunks
        merged_data = self.merge_resume_data(parsed_chunks)
        return merged_data

    def parse_job_description(self, text: str) -> Dict[str, Any]:
        """Parse job description text using LangChain and OpenAI."""
        # Create output parser
        parser = PydanticOutputParser(pydantic_object=JobDescription)

        # Create prompt template
        jd_template = """
        Extract structured information from the following job description. 
        Include all relevant information in the specified format.

        Job Description Text:
        {text}

        {format_instructions}
        """

        prompt = PromptTemplate(
            template=jd_template,
            input_variables=["text"],
            partial_variables={"format_instructions": parser.get_format_instructions()}
        )

        # Create chain
        chain = LLMChain(llm=self.llm, prompt=prompt)

        # Split text if it's too long
        texts = self.text_splitter.split_text(text)
        
        # Process first chunk (most important part of job description)
        result = chain.run(text=texts[0])
        
        try:
            parsed_data = parser.parse(result)
            return parsed_data.model_dump()
        except Exception as e:
            print(f"Error parsing job description data: {e}")
            return None

    def save_as_json(self, data: Dict[str, Any], file_type: str) -> Path:
        """Save parsed data as JSON file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{file_type}_{timestamp}.json"
        filepath = self.saved_details_path / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        
        print(f"Saved {file_type} data to {filepath}")
        return filepath

    def process_documents(self, resume_path: str, jd_path: str) -> None:
        """Process both resume and job description documents."""
        # Process Resume
        resume_text = self.extract_text_from_pdf(resume_path)
        if resume_text:
            resume_data = self.parse_resume(resume_text)
            if resume_data:
                self.save_as_json(resume_data, "resume")
            else:
                print("Failed to parse resume")
        else:
            print("Failed to process resume")

        # Process Job Description
        jd_text = self.extract_text_from_pdf(jd_path)
        if jd_text:
            jd_data = self.parse_job_description(jd_text)
            if jd_data:
                self.save_as_json(jd_data, "job_description")
            else:
                print("Failed to parse job description")
        else:
            print("Failed to process job description")

def main():
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not found in environment variables")
        print("Please create a .env file with your OpenAI API key")
        return

    parser = DocumentParser()
    
    # Get file paths from user
    resume_path = input("Enter the path to your resume PDF: ")
    jd_path = input("Enter the path to the job description PDF: ")
    
    # Process the documents
    parser.process_documents(resume_path, jd_path)

if __name__ == "__main__":
    main()