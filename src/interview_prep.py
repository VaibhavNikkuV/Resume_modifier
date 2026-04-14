"""Standalone Stage 2.5: generate interview-prep Q&A for fabricated projects.

Reads the latest `saved_details/job_analysis_*.json` (projects invented by
`job_related_projects.py`) and produces a PDF study guide at
`modified_resume/interview_prep.pdf`, with at least NUM_QUESTIONS Q&A pairs
per project so the candidate can defend those projects in a live interview.

Run standalone:

    python src/interview_prep.py

Not wired into `src/main.py` — integration is a deliberate follow-up.
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from xml.sax.saxutils import escape as xml_escape

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak,
)

from job_related_projects import get_latest_json_file, load_json_file


load_dotenv()


NUM_QUESTIONS = 10
CATEGORIES = ("technical", "architecture", "challenges", "impact", "behavioral", "follow_up")


class InterviewQA(BaseModel):
    question: str = Field(description="The interview question a hiring manager would ask.")
    answer: str = Field(
        description=(
            "A first-person answer the candidate can memorise. Specific, "
            "references the project's technologies, under ~120 words."
        )
    )
    category: str = Field(
        description=(
            "One of: technical, architecture, challenges, impact, behavioral, follow_up."
        )
    )


class ProjectInterviewPrep(BaseModel):
    project_name: str = Field(description="Name of the project these Q&As correspond to.")
    qa_pairs: List[InterviewQA] = Field(
        description=f"At least {NUM_QUESTIONS} question-answer pairs covering the required categories.",
    )


# ---------------------------------------------------------------------------
# LLM chain
# ---------------------------------------------------------------------------


_PROMPT_TEMPLATE = """
You are helping a job candidate prepare for an interview for the role of
{job_title} at {company}. The candidate will present the project below as
their own work. Your job is to generate realistic interview questions an
experienced hiring manager would ask about this project, together with
defensible first-person answers the candidate can memorise and deliver.

Project details:
- Name: {name}
- Role: {role}
- Duration: {duration}
- Description: {description}
- Technologies: {technologies}
- Achievements: {achievements}

Generate at least {num_questions} question-answer pairs. You MUST include at
least one question from EACH of these categories and label each pair with
its category:

- technical: concrete implementation details ("how did you build X?")
- architecture: design decisions, trade-offs, alternatives considered
  ("why did you pick Y over Z?")
- challenges: problems encountered and how they were resolved
- impact: measurable outcomes, metrics, business value
- behavioral: STAR-style collaboration, ownership, or conflict stories
- follow_up: scaling / "what would you do differently" / hypothetical
  extension questions

Answers must:
- Be written in the FIRST PERSON as if the candidate did the work.
- Be specific and reference the project's stated technologies by name.
- Stay under ~120 words each so they are memorable.
- Stay self-consistent across all Q&As so cross-questioning will not trip
  the candidate up.

{format_instructions}
"""


def _make_chain():
    """Build the prompt | llm | parser chain for a single project."""
    llm = ChatOpenAI(
        model_name="gpt-4.1-mini",
        temperature=0.4,
    )
    parser = PydanticOutputParser(pydantic_object=ProjectInterviewPrep)
    prompt = PromptTemplate(
        template=_PROMPT_TEMPLATE,
        input_variables=[
            "job_title",
            "company",
            "name",
            "role",
            "duration",
            "description",
            "technologies",
            "achievements",
            "num_questions",
        ],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )
    return prompt | llm | parser


def _project_inputs(project: Dict[str, Any], job_title: str, company: str) -> Dict[str, Any]:
    technologies = project.get("technologies") or []
    achievements = project.get("achievements") or []
    return {
        "job_title": job_title,
        "company": company,
        "name": project.get("name", "Unnamed project"),
        "role": project.get("role") or "Individual contributor",
        "duration": project.get("duration") or "Not specified",
        "description": project.get("description") or "",
        "technologies": ", ".join(technologies) if technologies else "Not specified",
        "achievements": "\n".join(f"- {a}" for a in achievements) if achievements else "None listed",
        "num_questions": NUM_QUESTIONS,
    }


def generate_project_qa(
    project: Dict[str, Any],
    job_title: str,
    company: str,
) -> ProjectInterviewPrep:
    """Invoke the chain once; retry once if the model returns fewer than NUM_QUESTIONS pairs."""
    chain = _make_chain()
    inputs = _project_inputs(project, job_title, company)
    result: ProjectInterviewPrep = chain.invoke(inputs)

    if len(result.qa_pairs) >= NUM_QUESTIONS:
        return result

    # Retry once with a stronger nudge — tack on a note via the description
    # field by re-invoking with the same inputs. (We can't mutate the prompt
    # mid-chain cleanly; the second call simply benefits from sampling jitter.)
    print(
        f"  Warning: model returned {len(result.qa_pairs)} Q&As for "
        f"'{project.get('name', '?')}' (wanted {NUM_QUESTIONS}); retrying once.",
        file=sys.stderr,
    )
    retry: ProjectInterviewPrep = chain.invoke(inputs)
    if len(retry.qa_pairs) < NUM_QUESTIONS:
        raise RuntimeError(
            f"LLM returned only {len(retry.qa_pairs)} Q&A pairs for project "
            f"'{project.get('name', '?')}' on retry; wanted at least {NUM_QUESTIONS}."
        )
    return retry


# ---------------------------------------------------------------------------
# PDF rendering
# ---------------------------------------------------------------------------


def _p(text: Any) -> str:
    """Escape a value for safe inclusion in a ReportLab Paragraph."""
    if text is None:
        return ""
    return xml_escape(str(text))


def _build_styles():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="PrepTitle",
            parent=styles["Heading1"],
            fontSize=18,
            textColor=colors.HexColor("#1a1a1a"),
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            name="PrepSubtitle",
            parent=styles["Normal"],
            fontSize=10,
            textColor=colors.grey,
            spaceAfter=14,
        )
    )
    styles.add(
        ParagraphStyle(
            name="ProjectHeading",
            parent=styles["Heading2"],
            fontSize=15,
            textColor=colors.HexColor("#0b3d91"),
            spaceBefore=4,
            spaceAfter=2,
        )
    )
    styles.add(
        ParagraphStyle(
            name="ProjectMeta",
            parent=styles["Italic"],
            fontSize=9,
            textColor=colors.grey,
            spaceAfter=10,
        )
    )
    styles.add(
        ParagraphStyle(
            name="QA_Question",
            parent=styles["Normal"],
            fontSize=11,
            textColor=colors.HexColor("#1a1a1a"),
            leading=14,
            spaceBefore=6,
            spaceAfter=2,
        )
    )
    styles.add(
        ParagraphStyle(
            name="QA_Answer",
            parent=styles["Normal"],
            fontSize=10,
            textColor=colors.HexColor("#333333"),
            leading=13,
            leftIndent=12,
            spaceAfter=4,
        )
    )
    return styles


def render_pdf(
    preps: List[ProjectInterviewPrep],
    projects_raw: List[Dict[str, Any]],
    job_title: str,
    company: str,
    output_path: Path,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        leftMargin=0.6 * inch,
        rightMargin=0.6 * inch,
        topMargin=0.6 * inch,
        bottomMargin=0.6 * inch,
    )
    styles = _build_styles()
    elements = []

    title_line = f"Interview Prep — {_p(job_title)} @ {_p(company)}"
    elements.append(Paragraph(title_line, styles["PrepTitle"]))
    subtitle = (
        f"Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} · "
        f"{len(preps)} projects · {sum(len(p.qa_pairs) for p in preps)} Q&A pairs"
    )
    elements.append(Paragraph(subtitle, styles["PrepSubtitle"]))

    for idx, prep in enumerate(preps):
        raw = projects_raw[idx] if idx < len(projects_raw) else {}
        elements.append(Paragraph(_p(prep.project_name), styles["ProjectHeading"]))

        role = raw.get("role") or ""
        duration = raw.get("duration") or ""
        technologies = ", ".join(raw.get("technologies") or [])
        meta_bits = [bit for bit in (role, duration, technologies) if bit]
        if meta_bits:
            elements.append(Paragraph(_p(" · ".join(meta_bits)), styles["ProjectMeta"]))

        for q_idx, qa in enumerate(prep.qa_pairs, start=1):
            q_line = f"<b>Q{q_idx}.</b> <i>[{_p(qa.category)}]</i> {_p(qa.question)}"
            elements.append(Paragraph(q_line, styles["QA_Question"]))
            elements.append(Paragraph(_p(qa.answer), styles["QA_Answer"]))

        if idx < len(preps) - 1:
            elements.append(PageBreak())

    doc.build(elements)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def _resolve_job_context(saved_details_dir: str) -> Dict[str, str]:
    """Best-effort load of the latest job_description_*.json for title/company."""
    jd_path = get_latest_json_file(saved_details_dir, "job_description")
    if not jd_path:
        return {"title": "your target role", "company": "the target company"}
    jd = load_json_file(jd_path) or {}
    return {
        "title": jd.get("title") or "your target role",
        "company": jd.get("company") or "the target company",
    }


def main() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not found in environment variables.", file=sys.stderr)
        print("Create a .env file with your OpenAI API key.", file=sys.stderr)
        sys.exit(1)

    saved_details_dir = "saved_details"
    if not Path(saved_details_dir).exists():
        print(
            f"Error: '{saved_details_dir}' directory not found. "
            "Run `python src/job_related_projects.py` first.",
            file=sys.stderr,
        )
        sys.exit(1)

    analysis_path = get_latest_json_file(saved_details_dir, "job_analysis")
    if not analysis_path:
        print(
            "Error: no job_analysis_*.json found in saved_details/. "
            "Run `python src/job_related_projects.py` first to generate the projects.",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"Loaded job analysis: {analysis_path}")
    analysis = load_json_file(analysis_path) or {}
    projects_raw: List[Dict[str, Any]] = analysis.get("projects") or []
    if not projects_raw:
        print("Warning: the latest job_analysis has no projects. Nothing to generate.", file=sys.stderr)
        sys.exit(1)

    job_ctx = _resolve_job_context(saved_details_dir)
    job_title = job_ctx["title"]
    company = job_ctx["company"]
    print(f"Target role: {job_title} @ {company}")

    preps: List[ProjectInterviewPrep] = []
    for i, project in enumerate(projects_raw, start=1):
        name = project.get("name", f"Project {i}")
        print(f"Generating Q&A for project {i}/{len(projects_raw)}: {name}")
        prep = generate_project_qa(project, job_title, company)
        preps.append(prep)

    output_dir = Path("modified_resume")
    output_path = output_dir / "interview_prep.pdf"
    print("Rendering PDF...")
    render_pdf(preps, projects_raw, job_title, company, output_path)

    total_qas = sum(len(p.qa_pairs) for p in preps)
    print(f"\nSaved interview prep PDF: {output_path}")
    print(f"  Projects: {len(preps)}  |  Q&A pairs: {total_qas}")


if __name__ == "__main__":
    main()
