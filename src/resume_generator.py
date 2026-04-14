import os
import json
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional

from pylatex import Document
from pylatex.utils import escape_latex


TEMPLATE_PATH = Path(__file__).parent / "resumeTemplate.txt"


def get_latest_json_file(directory: str, prefix: str) -> str:
    """Get the path to the latest JSON file with a specific prefix."""
    fixed_path = os.path.join(directory, f"{prefix}.json")
    if os.path.exists(fixed_path):
        return fixed_path

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
    """Join the per-category skill lists into comma-separated strings."""
    formatted_skills: Dict[str, str] = {}
    if skills_data.get("technical_skills"):
        formatted_skills["technical_skills"] = ", ".join(skills_data["technical_skills"])
    if skills_data.get("tools"):
        formatted_skills["tools"] = ", ".join(skills_data["tools"])
    if skills_data.get("soft_skills"):
        formatted_skills["soft_skills"] = ", ".join(skills_data["soft_skills"])
    if skills_data.get("domain_knowledge"):
        formatted_skills["domain_knowledge"] = ", ".join(skills_data["domain_knowledge"])
    return formatted_skills


def format_education(education_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normalise education entries into a single shape for the renderer."""
    formatted_education = []
    for education in education_list:
        formatted_education.append({
            "degree": education.get("degree", ""),
            "institution": education.get("institution") or "Not specified",
            "location": education.get("location", ""),
            # The parser emits `graduation_year`; older records used `graduation_date`.
            "graduation_date": education.get("graduation_date") or education.get("graduation_year", ""),
            "gpa": education.get("gpa") or "",
            "major": education.get("major") or "",
        })
    return formatted_education


def format_experience(experience_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normalise experience entries into a single shape for the renderer."""
    formatted_experience = []
    for experience in experience_list:
        # The parser emits `position` and `description`; accept the older
        # `title` / `responsibilities` field names as fallbacks.
        title = experience.get("title") or experience.get("position", "")
        company = experience.get("company", "")
        location = experience.get("location", "")

        if experience.get("date_range"):
            date_range = experience["date_range"]
        elif experience.get("start_date") or experience.get("end_date"):
            start = experience.get("start_date", "")
            end = experience.get("end_date") or ("Present" if experience.get("is_current") else "")
            date_range = f"{start} - {end}".strip(" -")
        else:
            date_range = experience.get("duration", "")

        bullets = experience.get("responsibilities") or experience.get("description") or []
        if isinstance(bullets, str):
            bullets = [bullets]
        bullets = list(bullets) + list(experience.get("achievements") or [])

        formatted_experience.append({
            "title": title,
            "company": company,
            "location": location,
            "date_range": date_range,
            "bullets": bullets,
        })

    return formatted_experience


def format_projects(projects_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normalise project entries into a single shape for the renderer."""
    formatted_projects = []
    for project in projects_list:
        entry = {
            "name": project.get("name", ""),
            "duration": project.get("duration", ""),
            "description": project.get("description", ""),
            "technologies": project.get("technologies", []) or [],
            "role": project.get("role", ""),
            "achievements": project.get("achievements", []) or [],
        }
        entry["technologies_str"] = ", ".join(entry["technologies"])
        formatted_projects.append(entry)
    return formatted_projects


def combine_resume_data(resume_data: Dict[str, Any], job_analysis_data: Dict[str, Any]) -> Dict[str, Any]:
    """Combine resume data with job-specific projects and skills."""
    return {
        "personal_info": resume_data.get("personal_info", {}),
        "education": format_education(resume_data.get("education", [])),
        "experience": format_experience(resume_data.get("experience", [])),
        "projects": format_projects(job_analysis_data.get("projects", [])),
        "skills": format_skills(job_analysis_data.get("skills", {})),
    }


# ---------------------------------------------------------------------------
# LaTeX rendering — built on top of src/resumeTemplate.txt (Jake Gutierrez
# template, MIT). The template's preamble + custom commands are reused
# verbatim; only the body sections are regenerated from the JSON data.
# ---------------------------------------------------------------------------


def parse_template(path: Path) -> str:
    r"""Return the preamble of the template (everything before \begin{document})."""
    text = path.read_text(encoding="utf-8")
    marker = r"\begin{document}"
    idx = text.find(marker)
    if idx == -1:
        raise ValueError(f"Template at {path} is missing a \\begin{{document}} line.")
    return text[:idx].rstrip() + "\n"


def _esc(text: Any) -> str:
    if text is None:
        return ""
    return escape_latex(str(text))


def _format_url(url: str, label: Optional[str] = None) -> str:
    r"""Build an \href{url}{\underline{label}} fragment, escaping URL-special chars."""
    if not url:
        return ""
    safe_url = url.replace("\\", "").replace("#", r"\#").replace("%", r"\%")
    display = label if label is not None else url
    for prefix in ("https://", "http://"):
        if display.startswith(prefix):
            display = display[len(prefix):]
            break
    return rf"\href{{{safe_url}}}{{\underline{{{_esc(display)}}}}}"


def render_heading(personal_info: Dict[str, Any]) -> str:
    name = _esc(personal_info.get("name", ""))

    parts: List[str] = []
    if personal_info.get("phone"):
        parts.append(_esc(personal_info["phone"]))
    if personal_info.get("email"):
        email = personal_info["email"]
        parts.append(rf"\href{{mailto:{email}}}{{\underline{{{_esc(email)}}}}}")
    if personal_info.get("linkedin"):
        url = personal_info["linkedin"]
        if not url.startswith("http"):
            url = "https://" + url
        parts.append(_format_url(url))
    if personal_info.get("github"):
        url = personal_info["github"]
        if not url.startswith("http"):
            url = "https://" + url
        parts.append(_format_url(url))

    contact_line = " $|$ ".join(parts)

    return (
        "%----------HEADING----------\n"
        "\\begin{center}\n"
        f"    \\textbf{{\\Huge \\scshape {name}}} \\\\ \\vspace{{1pt}}\n"
        f"    \\small {contact_line}\n"
        "\\end{center}\n"
    )


def render_education(education_list: List[Dict[str, Any]]) -> str:
    if not education_list:
        return ""

    lines = [
        "%-----------EDUCATION-----------",
        "\\section{Education}",
        "  \\resumeSubHeadingListStart",
    ]
    for edu in education_list:
        institution = edu.get("institution") or "Not specified"
        if institution == "Not specified":
            heading_left = _esc(edu.get("degree", ""))
            sub_left_raw = edu.get("major", "")
        else:
            heading_left = _esc(institution)
            degree = edu.get("degree", "")
            major = edu.get("major", "")
            if major and degree and major not in degree:
                sub_left_raw = f"{degree}, {major}"
            else:
                sub_left_raw = degree or major
        sub_left = _esc(sub_left_raw)

        if edu.get("gpa"):
            gpa_text = f"GPA: {_esc(edu['gpa'])}"
            sub_left = f"{sub_left} ({gpa_text})" if sub_left else gpa_text

        heading_right = _esc(edu.get("location", ""))
        sub_right = _esc(edu.get("graduation_date", ""))

        lines.append(
            "    \\resumeSubheading\n"
            f"      {{{heading_left}}}{{{heading_right}}}\n"
            f"      {{{sub_left}}}{{{sub_right}}}"
        )

    lines.append("  \\resumeSubHeadingListEnd")
    return "\n".join(lines) + "\n"


def render_experience(experience_list: List[Dict[str, Any]]) -> str:
    if not experience_list:
        return ""

    lines = [
        "%-----------EXPERIENCE-----------",
        "\\section{Experience}",
        "  \\resumeSubHeadingListStart",
    ]
    for job in experience_list:
        title = _esc(job.get("title", ""))
        date_range = _esc(job.get("date_range", ""))
        company = _esc(job.get("company", ""))
        location = _esc(job.get("location", ""))

        lines.append(
            "    \\resumeSubheading\n"
            f"      {{{title}}}{{{date_range}}}\n"
            f"      {{{company}}}{{{location}}}"
        )

        bullets = job.get("bullets", [])
        if bullets:
            lines.append("      \\resumeItemListStart")
            for bullet in bullets:
                lines.append(f"        \\resumeItem{{{_esc(bullet)}}}")
            lines.append("      \\resumeItemListEnd")

    lines.append("  \\resumeSubHeadingListEnd")
    return "\n".join(lines) + "\n"


def render_projects(projects_list: List[Dict[str, Any]]) -> str:
    if not projects_list:
        return ""

    lines = [
        "%-----------PROJECTS-----------",
        "\\section{Projects}",
        "    \\resumeSubHeadingListStart",
    ]
    for project in projects_list:
        name = _esc(project.get("name", ""))
        techs = _esc(project.get("technologies_str", ""))
        duration = _esc(project.get("duration", ""))

        if techs:
            heading = rf"\textbf{{{name}}} $|$ \emph{{{techs}}}"
        else:
            heading = rf"\textbf{{{name}}}"

        lines.append(
            "      \\resumeProjectHeading\n"
            f"          {{{heading}}}{{{duration}}}\n"
            "          \\resumeItemListStart"
        )
        if project.get("description"):
            lines.append(f"            \\resumeItem{{{_esc(project['description'])}}}")
        for achievement in project.get("achievements", []):
            lines.append(f"            \\resumeItem{{{_esc(achievement)}}}")
        lines.append("          \\resumeItemListEnd")

    lines.append("    \\resumeSubHeadingListEnd")
    return "\n".join(lines) + "\n"


def render_skills(skills_dict: Dict[str, str]) -> str:
    rows: List[str] = []
    if skills_dict.get("technical_skills"):
        rows.append(rf"\textbf{{Technical Skills}}{{: {_esc(skills_dict['technical_skills'])}}}")
    if skills_dict.get("tools"):
        rows.append(rf"\textbf{{Tools}}{{: {_esc(skills_dict['tools'])}}}")
    if skills_dict.get("soft_skills"):
        rows.append(rf"\textbf{{Soft Skills}}{{: {_esc(skills_dict['soft_skills'])}}}")
    if skills_dict.get("domain_knowledge"):
        rows.append(rf"\textbf{{Domain Knowledge}}{{: {_esc(skills_dict['domain_knowledge'])}}}")

    if not rows:
        return ""

    body = " \\\\\n     ".join(rows)
    return (
        "%-----------PROGRAMMING SKILLS-----------\n"
        "\\section{Technical Skills}\n"
        " \\begin{itemize}[leftmargin=0.15in, label={}]\n"
        "    \\small{\\item{\n"
        f"     {body}\n"
        "    }}\n"
        " \\end{itemize}\n"
    )


def build_latex_document(combined_data: Dict[str, Any], preamble: str) -> str:
    body_parts = [
        render_heading(combined_data.get("personal_info", {})),
        render_education(combined_data.get("education", [])),
        render_experience(combined_data.get("experience", [])),
        render_projects(combined_data.get("projects", [])),
        render_skills(combined_data.get("skills", {})),
    ]
    body = "\n".join(part for part in body_parts if part)
    return f"{preamble}\n\\begin{{document}}\n\n{body}\n\\end{{document}}\n"


class _RawDocument(Document):
    """A pylatex Document whose dumps() returns a pre-built LaTeX source verbatim.

    pylatex has no public API to compile an arbitrary external .tex; subclassing
    Document and overriding dumps() lets generate_pdf() drive the subprocess
    plumbing while we own the source.
    """

    def __init__(self, raw_source: str):
        super().__init__()
        self._raw_source = raw_source

    def dumps(self) -> str:
        return self._raw_source


def compile_latex_to_pdf(tex_source: str, output_dir: Path, basename: str) -> Path:
    if shutil.which("pdflatex") is None and shutil.which("latexmk") is None:
        raise RuntimeError(
            "No LaTeX engine found on PATH. Stage 3 needs pdflatex (or latexmk).\n"
            "  - macOS slim:  brew install --cask basictex     (~100 MB)\n"
            "  - macOS full:  brew install --cask mactex-no-gui\n"
            "After installing, open a new shell or run:\n"
            "  eval \"$(/usr/libexec/path_helper)\""
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    tex_path = output_dir / f"{basename}.tex"
    tex_path.write_text(tex_source, encoding="utf-8")

    compiler = "pdflatex" if shutil.which("pdflatex") else "latexmk"

    doc = _RawDocument(tex_source)
    try:
        doc.generate_pdf(
            str(output_dir / basename),
            clean_tex=False,
            compiler=compiler,
            silent=False,
        )
    except Exception as e:
        log_path = output_dir / f"{basename}.log"
        hint = f" See {log_path} for the LaTeX log." if log_path.exists() else ""
        raise RuntimeError(f"LaTeX compilation failed: {e}.{hint}") from e

    return output_dir / f"{basename}.pdf"


def main():
    try:
        saved_details_path = "saved_details"
        output_dir = "modified_resume"
        create_directory(output_dir)

        resume_file = get_latest_json_file(saved_details_path, "resume")
        print(f"Loading resume data from: {resume_file}")
        resume_data = load_json_file(resume_file)

        job_analysis_file = get_latest_json_file(saved_details_path, "job_analysis")
        print(f"Loading job analysis data from: {job_analysis_file}")
        job_analysis_data = load_json_file(job_analysis_file)

        if not resume_data:
            raise ValueError("Failed to load resume data. Make sure Resume_and_JD_parse.py has been run.")
        if not job_analysis_data:
            raise ValueError("Failed to load job analysis data. Make sure job_related_projects.py has been run.")

        print("Combining resume data with job-specific projects and skills...")
        combined_data = combine_resume_data(resume_data, job_analysis_data)

        print("Building LaTeX document from template...")
        preamble = parse_template(TEMPLATE_PATH)
        tex_source = build_latex_document(combined_data, preamble)

        print("Compiling LaTeX to PDF (pylatex)...")
        pdf_path = compile_latex_to_pdf(tex_source, Path(output_dir), "modified_resume")

        print("\nResume generation completed successfully!")
        print(f"  PDF:   {pdf_path}")
        print(f"  LaTeX: {pdf_path.with_suffix('.tex')}")

    except Exception as e:
        print(f"Error generating resume: {e}")


if __name__ == "__main__":
    main()
