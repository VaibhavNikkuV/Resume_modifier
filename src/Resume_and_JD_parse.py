import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from langchain_openai import ChatOpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List, Optional

# Load environment variables
load_dotenv()

# Define output schemas using Pydantic
class PersonalInfo(BaseModel):
    name: str = Field(description="Full name of the person")
    email: Optional[str] = Field(description="Email address")
    phone: Optional[str] = Field(description="Phone number")
    location: Optional[str] = Field(description="Current location")
    linkedin: Optional[str] = Field(description="LinkedIn profile URL")

class Education(BaseModel):
    degree: str = Field(description="Degree name")
    institution: str = Field(description="Institution name")
    graduation_year: Optional[str] = Field(description="Year of graduation")
    gpa: Optional[str] = Field(description="GPA if mentioned")
    major: Optional[str] = Field(description="Field of study/Major")

class Experience(BaseModel):
    company: str = Field(description="Company name")
    position: str = Field(description="Job title/position")
    duration: str = Field(description="Duration of employment")
    description: List[str] = Field(description="List of responsibilities and achievements")

class ResumeData(BaseModel):
    personal_info: PersonalInfo = Field(description="Personal information of the candidate")
    education: List[Education] = Field(description="List of educational qualifications")
    experience: List[Experience] = Field(description="List of work experiences")
    skills: List[str] = Field(description="List of technical and soft skills")

class JobDescription(BaseModel):
    title: str = Field(description="Job title")
    company: str = Field(description="Company name")
    location: Optional[str] = Field(description="Job location")
    requirements: List[str] = Field(description="List of job requirements")
    responsibilities: List[str] = Field(description="List of job responsibilities")
    qualifications: List[str] = Field(description="List of required qualifications")
    preferred_skills: List[str] = Field(description="List of preferred skills")

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

    def parse_resume(self, text: str) -> Dict[str, Any]:
        """Parse resume text using LangChain and OpenAI."""
        # Create output parser
        parser = PydanticOutputParser(pydantic_object=ResumeData)

        # Create prompt template
        resume_template = """
        Extract structured information from the following resume text. 
        Include all relevant information in the specified format.

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

        # Split text if it's too long
        texts = self.text_splitter.split_text(text)
        
        # Process first chunk (most important part of resume)
        result = chain.run(text=texts[0])
        
        try:
            parsed_data = parser.parse(result)
            return parsed_data.model_dump()
        except Exception as e:
            print(f"Error parsing resume data: {e}")
            return None

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