import os
import json
import glob
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv()

class Project(BaseModel):
    name: str = Field(description="Name of the project")
    duration: str = Field(description="Estimated duration of the project (e.g., '2 months')")
    description: str = Field(description="Detailed description of the project that aligns with the job requirements")
    technologies: List[str] = Field(description="Technologies, tools, and languages used, relevant to the job description")
    role: str = Field(description="Role in the project that demonstrates skills required in the job")
    url: Optional[str] = Field(description="Project URL or repository link if applicable", default=None)
    achievements: List[str] = Field(description="Key achievements or outcomes of the project that align with job requirements")

class ProjectSuggestions(BaseModel):
    projects: List[Project] = Field(description="List of suggested projects relevant to the job description")

def get_latest_json_file(directory: str, prefix: str) -> Optional[str]:
    """Get the most recent JSON file with a given prefix from a directory."""
    files = glob.glob(os.path.join(directory, f"{prefix}_*.json"))
    if not files:
        return None
    return max(files, key=os.path.getctime)

def load_json_file(file_path: str) -> Dict[str, Any]:
    """Load a JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading JSON file: {e}")
        return {}

def generate_project_suggestions(job_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate project suggestions based on job description."""
    # Initialize LLM
    llm = ChatOpenAI(
        model_name="gpt-4-turbo-preview",
        temperature=0.7,
    )
    
    # Create output parser
    parser = PydanticOutputParser(pydantic_object=ProjectSuggestions)
    
    # Create prompt template
    template = """
    You are a career advisor helping a job applicant create project ideas that align with a job description.
    
    Below is a job description. Your task is to generate {num_projects} project ideas that would demonstrate 
    the skills and experiences required for this position. Each project should be realistic, detailed, and 
    showcase relevant technologies and achievements.
    
    Job Title: {title}
    Company: {company}
    
    Job Requirements:
    {requirements}
    
    Job Responsibilities:
    {responsibilities}
    
    Preferred Skills:
    {preferred_skills}
    
    Generate projects that:
    1. Demonstrate the required technical skills
    2. Align with the job responsibilities
    3. Show problem-solving abilities in the relevant domain
    4. Highlight achievements that would impress the hiring manager
    5. Include relevant technologies from the job description
    
    {format_instructions}
    """
    
    # Format job data for prompt
    requirements_text = "\n".join([f"- {req}" for req in job_data.get("requirements", [])])
    responsibilities_text = "\n".join([f"- {resp}" for resp in job_data.get("responsibilities", [])])
    preferred_skills_text = "\n".join([f"- {skill}" for skill in job_data.get("preferred_skills", [])])
    
    prompt = PromptTemplate(
        template=template,
        input_variables=["title", "company", "requirements", "responsibilities", "preferred_skills", "num_projects"],
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    
    # Create chain using the pipe operator
    chain = prompt | llm | parser
    
    # Run chain
    result = chain.invoke({
        "title": job_data.get("title", "Unnamed Position"),
        "company": job_data.get("company", "Unnamed Company"),
        "requirements": requirements_text,
        "responsibilities": responsibilities_text,
        "preferred_skills": preferred_skills_text,
        "num_projects": 3  # Generate 3 project suggestions
    })
    
    return result.model_dump()

def save_as_json(data: Dict[str, Any], file_path: Path) -> None:
    """Save data as JSON file."""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
    
    print(f"Saved project suggestions to {file_path}")

def main():
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not found in environment variables")
        print("Please create a .env file with your OpenAI API key")
        return
    
    # Set up directories
    saved_details_path = Path("saved_details")
    if not saved_details_path.exists():
        print(f"Error: '{saved_details_path}' directory not found.")
        print("Please run Resume_and_JD_parse.py first to generate job description data.")
        return
    
    # Get the latest job description file
    latest_jd_file = get_latest_json_file(saved_details_path, "job_description")
    if not latest_jd_file:
        print("No job description file found in the saved_details directory.")
        print("Please run Resume_and_JD_parse.py first to generate job description data.")
        return
    
    print(f"Using job description file: {latest_jd_file}")
    job_data = load_json_file(latest_jd_file)
    
    if not job_data:
        print("Failed to load job description data.")
        return
    
    # Generate project suggestions
    print("Generating project suggestions based on job description...")
    project_suggestions = generate_project_suggestions(job_data)
    
    # Save the project suggestions
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = saved_details_path / f"project_suggestions_{timestamp}.json"
    save_as_json(project_suggestions, output_file)
    
    print("Project suggestions generated successfully!")
    print(f"Number of projects generated: {len(project_suggestions['projects'])}")
    for i, project in enumerate(project_suggestions['projects'], 1):
        print(f"\nProject {i}: {project['name']}")
        print(f"Technologies: {', '.join(project['technologies'])}")

if __name__ == "__main__":
    main()