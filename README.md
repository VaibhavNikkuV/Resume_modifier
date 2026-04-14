# Resume Modifier

An AI-powered tool designed to help job seekers create tailored resumes for specific job postings. The tool leverages OpenAI's advanced language models to parse both resumes and job descriptions, extract structured information, generate job-specific projects, create an ATS-friendly resume optimized for each application, and produce an interview prep study guide so you can confidently defend the generated projects in a real interview.

## Features

- **AI-powered Resume Analysis**: Extract structured information from your existing resume
- **Job Description Parsing**: Identify key requirements, responsibilities, and skills from job postings
- **Personalized Project Suggestions**: Generate job-specific projects that align with job requirements
- **Skill Matching and Enhancement**: Extract and categorize relevant skills for the target job
- **ATS-friendly Resume Generation**: Create a LaTeX-typeset PDF resume optimized for Applicant Tracking Systems
- **Interview Prep Study Guide**: Generate a PDF with ≥10 interview Q&A pairs per fabricated project (covering technical, architecture, challenges, impact, behavioral, and follow-up categories) so you can memorise defensible, self-consistent answers before the interview
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
- A system LaTeX install (`pdflatex` or `latexmk` on `PATH`) — required for Step 3. On macOS: `brew install --cask mactex-no-gui` (full) or `brew install --cask basictex` (slim, ~100 MB), then `eval "$(/usr/libexec/path_helper)"` in a new shell.

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
4. Create an ATS-optimized resume in LaTeX, then compile it to PDF
5. Generate an interview prep PDF with ≥10 Q&A pairs per fabricated project
6. Save the final results in the `modified_resume` directory:
   - `modified_resume.pdf` (and the `modified_resume.tex` source next to it)
   - `interview_prep.pdf`

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

#### 4. Generate Interview Prep Q&A PDF

```bash
python src/interview_prep.py
```

Reads the most recent `saved_details/job_analysis_*.json` and writes `modified_resume/interview_prep.pdf`. Safe to run standalone after Step 2 — it does not depend on the resume generator or on a LaTeX install.

## Directory Structure

- `src/`: Source code files
  - `main.py`: Main script to run the entire workflow
  - `Resume_and_JD_parse.py`: Script for parsing resume and job description PDFs
  - `job_related_projects.py`: Script for generating job-specific projects and skills
  - `resume_generator.py`: Script for creating the optimized resume PDF (LaTeX → PDF)
  - `interview_prep.py`: Script for generating the interview prep Q&A PDF
  - `resumeTemplate.txt`: Jake Gutierrez LaTeX resume template (MIT) used as the design base
- `saved_details/`: JSON files containing parsed data (created at runtime)
- `modified_resume/`: Output directory for generated resume and interview prep PDFs (created at runtime)

## Technical Details

- **PDF Processing**: PyPDF2 for extracting text from PDF documents
- **AI Integration**: LangChain for OpenAI model integration
- **Data Validation**: Pydantic for structured data validation
- **Resume PDF Generation**: LaTeX (Jake Gutierrez template) compiled via `pylatex` and a system `pdflatex` install
- **Interview Prep PDF Generation**: ReportLab for rendering the Q&A study guide
- **Environment Management**: python-dotenv for API key handling

## Recent Updates

- **Interview Prep Study Guide**: Added Step 4 — `interview_prep.py` generates a PDF with ≥10 Q&A pairs per fabricated project so you can defend them in a real interview
- **LaTeX-based Resume Generation**: Step 3 now emits LaTeX (Jake Gutierrez template) and compiles it via `pylatex` + `pdflatex` for a cleaner, more ATS-friendly layout
- **Unified Workflow**: `main.py` automates all four steps end-to-end
- **Enhanced Error Handling**: Better validation and null value handling
- **Improved JSON Structure**: More consistent data format
- **Smart Chunking**: Better handling of large documents

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Contact

Vaibhav Arya - [@VaibhavNikkuV](https://github.com/VaibhavNikkuV)

Project Link: [https://github.com/VaibhavNikkuV/Resume_modifier](https://github.com/VaibhavNikkuV/Resume_modifier) 
