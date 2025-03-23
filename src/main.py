import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

# Import modules from other files
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from Resume_and_JD_parse import DocumentParser

def print_separator():
    """Print a separator line for better readability."""
    print("\n" + "="*80 + "\n")

def check_prerequisites():
    """Check if all prerequisites are met before running the workflow."""
    # Check for .env file
    if not os.path.exists('.env'):
        print("Error: .env file not found in the project root directory.")
        print("Please create a .env file with your OpenAI API key:")
        print("OPENAI_API_KEY=your_key_here")
        print("OPENAI_MODEL=gpt-4-turbo-preview")
        return False
    
    # Check if OpenAI API key is set
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not found in environment variables")
        print("Please make sure your .env file has a valid OpenAI API key")
        return False
    
    # Ensure required directories exist
    saved_details_path = Path("saved_details")
    modified_resume_path = Path("modified_resume")
    
    saved_details_path.mkdir(exist_ok=True)
    modified_resume_path.mkdir(exist_ok=True)
    
    return True

def get_resume_jd_paths():
    """Get paths to resume and job description PDFs from user input."""
    print_separator()
    print("Please provide the paths to your resume and job description PDFs.")
    print("These paths can be absolute or relative to the project root directory.")
    print_separator()
    
    while True:
        resume_path = input("Enter the path to your resume PDF: ")
        if os.path.exists(resume_path) and resume_path.lower().endswith('.pdf'):
            break
        print("Error: File not found or not a PDF. Please provide a valid path.")
    
    while True:
        jd_path = input("Enter the path to the job description PDF: ")
        if os.path.exists(jd_path) and jd_path.lower().endswith('.pdf'):
            break
        print("Error: File not found or not a PDF. Please provide a valid path.")
    
    return resume_path, jd_path

def run_script(script_name, step_number, step_description):
    """Run a Python script and capture its output."""
    print_separator()
    print(f"Step {step_number}: {step_description}")
    
    try:
        # Import and run the script dynamically
        if script_name == "job_related_projects":
            import job_related_projects
            # Run the main function from the module
            job_related_projects.main()
        elif script_name == "resume_generator":
            import resume_generator
            # Run the main function from the module
            resume_generator.main()
        print(f"✓ {step_description} completed successfully!")
        return True
    except Exception as e:
        print(f"Error running {script_name}.py: {e}")
        return False

def main():
    """Main function to run the entire workflow."""
    print_separator()
    print("                      Resume Modifier - Automated Workflow")
    print_separator()
    print("This script will automate the entire process of:")
    print("1. Parsing your resume and job description")
    print("2. Generating job-specific projects and skills")
    print("3. Creating a modified resume PDF optimized for the job")
    print("\nThe final resume will be saved in the 'modified_resume' directory.")
    print_separator()
    
    # Check prerequisites
    if not check_prerequisites():
        return
    
    # Get file paths
    resume_path, jd_path = get_resume_jd_paths()
    
    # Step 1: Parse resume and job description
    print_separator()
    print("Step 1: Parsing resume and job description...")
    parser = DocumentParser()
    parser.process_documents(resume_path, jd_path)
    print("✓ Resume and job description parsed successfully!")
    
    # Give the system time to write files
    time.sleep(1)
    
    # Step 2: Generate job-related projects and skills
    if not run_script("job_related_projects", 2, "Generating job-related projects and skills"):
        return
    
    # Give the system time to write files
    time.sleep(1)
    
    # Step 3: Generate modified resume
    if not run_script("resume_generator", 3, "Creating modified resume optimized for the job"):
        return
    
    print_separator()
    print("All steps completed successfully! Your resume is now optimized for the job.")
    print("Good luck with your application!")
    print_separator()

if __name__ == "__main__":
    main() 