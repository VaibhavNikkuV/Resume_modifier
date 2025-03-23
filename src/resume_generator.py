import os
import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, ListFlowable, ListItem
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

def get_latest_json_file(directory: str, prefix: str) -> str:
    """Get the path to the latest JSON file with a specific prefix."""
    # First check for fixed filename
    fixed_path = os.path.join(directory, f"{prefix}.json")
    if os.path.exists(fixed_path):
        return fixed_path
    
    # Then check for timestamped files
    files = [f for f in os.listdir(directory) if f.startswith(prefix) and f.endswith(".json")]
    if not files:
        raise FileNotFoundError(f"No {prefix} files found in {directory}")
    
    files_with_time = [(f, os.path.getmtime(os.path.join(directory, f))) for f in files]
    latest_file = max(files_with_time, key=lambda x: x[1])[0]
    return os.path.join(directory, latest_file)

def load_json_file(file_path: str) -> Dict[str, Any]:
    """Load a JSON file and return its contents."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading JSON file {file_path}: {e}")
        return {}

def create_directory(dir_path: str) -> None:
    """Create directory if it doesn't exist."""
    path = Path(dir_path)
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")

def format_skills(skills_data: Dict[str, List[str]]) -> Dict[str, str]:
    """Format skills into well-organized strings for the resume."""
    formatted_skills = {}
    
    # Format technical skills
    if "technical_skills" in skills_data:
        formatted_skills["technical_skills"] = ", ".join(skills_data["technical_skills"])
    
    # Format tools/technologies
    if "tools" in skills_data:
        formatted_skills["tools"] = ", ".join(skills_data["tools"])
    
    # Format soft skills
    if "soft_skills" in skills_data:
        formatted_skills["soft_skills"] = ", ".join(skills_data["soft_skills"])
    
    # Format domain knowledge
    if "domain_knowledge" in skills_data:
        formatted_skills["domain_knowledge"] = ", ".join(skills_data["domain_knowledge"])
    
    return formatted_skills

def format_education(education_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Format education entries for the resume."""
    formatted_education = []
    
    for education in education_list:
        entry = {
            "degree": education.get("degree", ""),
            "institution": education.get("institution", "Not specified"),
            "location": education.get("location", ""),
            "graduation_date": education.get("graduation_date", ""),
            "gpa": education.get("gpa", "")
        }
        
        # Create a formatted display string
        display_parts = []
        display_parts.append(f"{entry['degree']}")
        if entry['institution'] != "Not specified":
            display_parts.append(f"{entry['institution']}")
        if entry['location']:
            display_parts.append(f"{entry['location']}")
        if entry['graduation_date']:
            display_parts.append(f"Graduation: {entry['graduation_date']}")
        if entry['gpa']:
            display_parts.append(f"GPA: {entry['gpa']}")
        
        entry["display"] = " | ".join(display_parts)
        formatted_education.append(entry)
    
    return formatted_education

def format_experience(experience_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Format experience entries for the resume."""
    formatted_experience = []
    
    for experience in experience_list:
        entry = {
            "title": experience.get("title", ""),
            "company": experience.get("company", ""),
            "location": experience.get("location", ""),
            "start_date": experience.get("start_date", ""),
            "end_date": experience.get("end_date", "Present" if experience.get("is_current", False) else experience.get("end_date", "")),
            "responsibilities": experience.get("responsibilities", []),
            "achievements": experience.get("achievements", [])
        }
        
        # Create a formatted date range
        if entry["start_date"] and (entry["end_date"] or entry["end_date"] == "Present"):
            entry["date_range"] = f"{entry['start_date']} - {entry['end_date']}"
        else:
            entry["date_range"] = ""
        
        formatted_experience.append(entry)
    
    # Sort by date (most recent first)
    return sorted(formatted_experience, key=lambda x: x.get("end_date", "Present"), reverse=True)

def format_projects(projects_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Format project entries for the resume."""
    formatted_projects = []
    
    for project in projects_list:
        entry = {
            "name": project.get("name", ""),
            "duration": project.get("duration", ""),
            "description": project.get("description", ""),
            "technologies": project.get("technologies", []),
            "role": project.get("role", ""),
            #"url": project.get("url", ""),
            "achievements": project.get("achievements", [])
        }
        
        # Create a formatted technologies string
        entry["technologies_str"] = ", ".join(entry["technologies"])
        
        formatted_projects.append(entry)
    
    return formatted_projects

def generate_pdf_resume(resume_data: Dict[str, Any], output_path: str) -> None:
    """Generate PDF resume directly using ReportLab."""
    # Set up the document
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=0.2*inch,
        rightMargin=0.2*inch,
        topMargin=0.2*inch,
        bottomMargin=0.2*inch
    )
    
    # Get styles
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='Center',
        parent=styles['Normal'],
        alignment=1,  # 0=left, 1=center, 2=right
    ))
    styles.add(ParagraphStyle(
        name='SectionHeading',
        parent=styles['Heading2'],
        textColor=colors.darkblue,
        spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name='JobHeading',
        parent=styles['Heading3'],
        textColor=colors.black,
        fontSize=12,
        spaceAfter=2,
    ))
    
    # Elements to add to the document
    elements = []
    
    # Personal Info
    personal_info = resume_data.get("personal_info", {})
    elements.append(Paragraph(personal_info.get("name", ""), styles['Heading1']))
    elements.append(Paragraph(personal_info.get("title", ""), styles['Center']))
    
    # Contact Info
    contact_parts = []
    if personal_info.get("email"):
        contact_parts.append(personal_info["email"])
    if personal_info.get("phone"):
        contact_parts.append(personal_info["phone"])
    if personal_info.get("location"):
        contact_parts.append(personal_info["location"])
    if personal_info.get("linkedin"):
        contact_parts.append(f"LinkedIn: {personal_info['linkedin']}")
    if personal_info.get("github"):
        contact_parts.append(f"GitHub: {personal_info['github']}")
    
    contact_text = " | ".join(contact_parts)
    elements.append(Paragraph(contact_text, styles['Center']))
    elements.append(Spacer(1, 0.2*inch))
    
    # Summary if available
    if personal_info.get("summary"):
        elements.append(Paragraph("Professional Summary", styles['SectionHeading']))
        elements.append(Paragraph(personal_info["summary"], styles['Normal']))
        elements.append(Spacer(1, 0.2*inch))
    
    # Skills
    skills = resume_data.get("skills", {})
    if skills:
        elements.append(Paragraph("Skills", styles['SectionHeading']))
        
        skill_data = []
        if skills.get("technical_skills"):
            skill_data.append(["Technical Skills:", skills["technical_skills"]])
        if skills.get("tools"):
            skill_data.append(["Tools & Technologies:", skills["tools"]])
        if skills.get("soft_skills"):
            skill_data.append(["Soft Skills:", skills["soft_skills"]])
        if skills.get("domain_knowledge"):
            skill_data.append(["Domain Knowledge:", skills["domain_knowledge"]])
        
        if skill_data:
            skill_table = Table(skill_data, colWidths=[1.5*inch, 5*inch])
            skill_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('TOPPADDING', (0, 0), (-1, -1), 2),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ]))
            elements.append(skill_table)
            elements.append(Spacer(1, 0.2*inch))
    
    # Experience
    experience = resume_data.get("experience", [])
    if experience:
        elements.append(Paragraph("Experience", styles['SectionHeading']))
        
        for job in experience:
            job_title = f"{job.get('title', '')} - {job.get('company', '')}"
            elements.append(Paragraph(job_title, styles['JobHeading']))
            
            date_location = []
            if job.get("date_range"):
                date_location.append(job["date_range"])
            if job.get("location"):
                date_location.append(job["location"])
            
            if date_location:
                elements.append(Paragraph(" | ".join(date_location), styles['Italic']))
            
            # Responsibilities and achievements
            if job.get("responsibilities") or job.get("achievements"):
                items = []
                for resp in job.get("responsibilities", []):
                    items.append(ListItem(Paragraph(resp, styles['Normal'])))
                for achievement in job.get("achievements", []):
                    items.append(ListItem(Paragraph(achievement, styles['Normal'])))
                
                if items:
                    elements.append(ListFlowable(items, bulletType='bullet', leftIndent=20))
            
            elements.append(Spacer(1, 0.1*inch))
    
    # Projects
    projects = resume_data.get("projects", [])
    if projects:
        elements.append(Paragraph("Projects", styles['SectionHeading']))
        
        for project in projects:
            project_header = project.get("name", "")
            if project.get("duration"):
                project_header += f" ({project['duration']})"
            elements.append(Paragraph(project_header, styles['JobHeading']))
            
            if project.get("role"):
                elements.append(Paragraph(f"<b>Role:</b> {project['role']}", styles['Normal']))
            
            if project.get("description"):
                elements.append(Paragraph(project['description'], styles['Normal']))
            
            if project.get("technologies_str"):
                elements.append(Paragraph(f"<b>Technologies:</b> {project['technologies_str']}", styles['Normal']))
            
            if project.get("achievements"):
                items = []
                for achievement in project["achievements"]:
                    items.append(ListItem(Paragraph(achievement, styles['Normal'])))
                
                if items:
                    elements.append(ListFlowable(items, bulletType='bullet', leftIndent=20))
            
            if project.get("url"):
                elements.append(Paragraph(f"<b>Link:</b> {project['url']}", styles['Normal']))
            
            elements.append(Spacer(1, 0.1*inch))
    
    # Education
    education = resume_data.get("education", [])
    if education:
        elements.append(Paragraph("Education", styles['SectionHeading']))
        
        for edu in education:
            if edu.get("display"):
                elements.append(Paragraph(edu["display"], styles['Normal']))
                elements.append(Spacer(1, 0.05*inch))
    
    # Build the PDF
    doc.build(elements)

def combine_resume_data(resume_data: Dict[str, Any], job_analysis_data: Dict[str, Any]) -> Dict[str, Any]:
    """Combine resume data with job-specific projects and skills."""
    combined_data = {
        "personal_info": resume_data.get("personal_info", {}),
        "education": format_education(resume_data.get("education", [])),
        "experience": format_experience(resume_data.get("experience", [])),
        "projects": format_projects(job_analysis_data.get("projects", [])),
        "skills": format_skills(job_analysis_data.get("skills", {}))
    }
    
    return combined_data

def main():
    try:
        # Set up directories
        saved_details_path = "saved_details"
        output_dir = "modified_resume"
        create_directory(output_dir)
        
        # Load resume data
        resume_file = get_latest_json_file(saved_details_path, "resume")
        print(f"Loading resume data from: {resume_file}")
        resume_data = load_json_file(resume_file)
        
        # Load job analysis data
        job_analysis_file = get_latest_json_file(saved_details_path, "job_analysis")
        print(f"Loading job analysis data from: {job_analysis_file}")
        job_analysis_data = load_json_file(job_analysis_file)
        
        # Check if data was loaded successfully
        if not resume_data:
            raise ValueError("Failed to load resume data. Make sure Resume_and_JD_parse.py has been run.")
        
        if not job_analysis_data:
            raise ValueError("Failed to load job analysis data. Make sure job_related_projects.py has been run.")
        
        # Combine the data
        print("Combining resume data with job-specific projects and skills...")
        combined_data = combine_resume_data(resume_data, job_analysis_data)
        
        # Generate timestamp for file names
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Generate file paths
        standard_pdf_path = os.path.join(output_dir, "modified_resume.pdf")
        
        # Generate PDF directly
        print("Generating PDF resume...")
        generate_pdf_resume(combined_data, standard_pdf_path)
        
        print("\nResume generation completed successfully!")
        print(f"Resume saved as PDF in {output_dir}:")
        print(f"  - {os.path.basename(standard_pdf_path)}")
        
    except Exception as e:
        print(f"Error generating resume: {e}")

if __name__ == "__main__":
    main() 