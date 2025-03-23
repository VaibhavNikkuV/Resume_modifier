# Resume Modifier

An AI-powered tool designed to help job seekers create tailored resumes for specific job postings. The tool leverages OpenAI's advanced language models to parse both resumes and job descriptions, extract structured information, generate job-specific projects, and create an ATS-friendly resume optimized for each application.

## Features

- **AI-powered Resume Analysis**: Extract structured information from your existing resume
- **Job Description Parsing**: Identify key requirements, responsibilities, and skills from job postings
- **Personalized Project Suggestions**: Generate job-specific projects that align with job requirements
- **Skill Matching and Enhancement**: Extract and categorize relevant skills for the target job
- **ATS-friendly Resume Generation**: Create a PDF resume optimized for Applicant Tracking Systems
- **One-Command Workflow**: Complete end-to-end process with a single command
- **Comprehensive Data Extraction**:
  - Personal information (name, email, phone, links)
  - Education details with institution and dates
  - Work experience with responsibilities
  - Projects with technologies and achievements
  - Skills categorized by type (technical, soft, domain)

## Getting Started

### Prerequisites

- Python 3.8 or higher
- OpenAI API key

### Installation

1. Clone the repository:
```bash
git clone https://github.com/VaibhavNikkuV/Resume_modifier.git
```

2. Navigate to the project directory:
```bash
cd Resume_modifier
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root with your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4-turbo-preview
```

## Usage

### Automated Workflow (Recommended)

Run the entire process with a single command:

```bash
python src/main.py
```

The script will:
1. Ask for paths to your resume and job description PDFs
2. Parse both documents and extract structured data
3. Generate job-specific projects and analyze required skills
4. Create an ATS-optimized resume in PDF format
5. Save the final result as `modified_resume.pdf` in the `modified_resume` directory

### Step-by-Step Process (Alternative)

If you prefer to run each step individually:

#### 1. Parse Resume and Job Description

```bash
python src/Resume_and_JD_parse.py
```

Enter the paths to your resume and job description PDFs when prompted.

#### 2. Generate Job-Specific Projects and Skills

```bash
python src/job_related_projects.py
```

#### 3. Generate ATS-Friendly Resume

```bash
python src/resume_generator.py
```

## Directory Structure

- `src/`: Source code files
  - `main.py`: Main script to run the entire workflow
  - `Resume_and_JD_parse.py`: Script for parsing resume and job description PDFs
  - `job_related_projects.py`: Script for generating job-specific projects and skills
  - `resume_generator.py`: Script for creating the optimized resume PDF
- `saved_details/`: JSON files containing parsed data (created at runtime)
- `modified_resume/`: Output directory for generated resumes (created at runtime)

## Technical Details

- **PDF Processing**: PyPDF2 for extracting text from PDF documents
- **AI Integration**: LangChain for OpenAI model integration
- **Data Validation**: Pydantic for structured data validation
- **PDF Generation**: ReportLab for direct PDF creation
- **Environment Management**: python-dotenv for API key handling

## Recent Updates

- **Unified Workflow**: Added `main.py` to automate the entire process
- **Model Improvements**: Updated to use gpt-4-turbo-preview for better results
- **Enhanced Error Handling**: Better validation and null value handling
- **Direct PDF Generation**: Streamlined the output process
- **Improved JSON Structure**: More consistent data format
- **Smart Chunking**: Better handling of large documents

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

Vaibhav Arya - [@VaibhavNikkuV](https://github.com/VaibhavNikkuV)

Project Link: [https://github.com/VaibhavNikkuV/Resume_modifier](https://github.com/VaibhavNikkuV/Resume_modifier) 
