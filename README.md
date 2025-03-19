# Resume Modifier

An AI-powered tool designed to help users modify and manage their resumes efficiently using advanced natural language processing and machine learning techniques. The tool can parse both resumes and job descriptions, extracting structured information for better analysis and comparison.

## Features

- AI-powered resume and job description parsing using LangChain and OpenAI
- Comprehensive data extraction including:
  - Personal information
  - Education details
  - Work experience
  - Projects with detailed information
  - Technical and soft skills
- Intelligent chunking for processing large documents
- Structured JSON output for parsed data
- Duplicate detection and removal
- Robust error handling and validation
- Support for PDF document processing

## Getting Started

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Virtual environment (recommended)
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

3. Create and activate a virtual environment:
```bash
# On Windows
python -m venv venv
.\venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

5. Create a `.env` file in the project root and add your OpenAI API key:
```bash
OPENAI_API_KEY=your_api_key_here
```

## Technical Stack

- **Python**: Core programming language
- **LangChain**: For AI model integration and document processing
- **OpenAI GPT-4**: For intelligent text parsing and analysis
- **PyPDF2**: For PDF document processing
- **Pydantic**: For data validation and settings management
- **python-dotenv**: For environment variable management

## Usage

1. Place your resume and job description in PDF format in an accessible location.

2. Run the parser script:
```bash
python src/Resume_and_JD_parse.py
```

3. When prompted, enter the paths to your resume and job description PDFs.

4. The script will process both documents and save the parsed data as JSON files in the `saved_details` directory.

### Output Format

The parser generates structured JSON files with the following information:

#### Resume Output
- Personal Information (name, email, phone, location, LinkedIn)
- Education (degree, institution, graduation year, GPA, major)
- Work Experience (company, position, duration, responsibilities)
- Projects (name, duration, description, technologies, role, URL, achievements)
- Skills (technical and soft skills)

#### Job Description Output
- Job Title
- Company Name
- Location
- Requirements
- Responsibilities
- Qualifications
- Preferred Skills

## Recent Updates

- Added comprehensive project information extraction
- Implemented multi-chunk processing for better data extraction
- Enhanced error handling and validation
- Added support for handling missing or null values
- Improved duplicate detection and removal
- Updated package dependencies for better compatibility

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

Vaibhav Arya - [@VaibhavNikkuV](https://github.com/VaibhavNikkuV)

Project Link: [https://github.com/VaibhavNikkuV/Resume_modifier](https://github.com/VaibhavNikkuV/Resume_modifier)