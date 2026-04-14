# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

Install dependencies (the project has both a `requirements.txt` and a nearly-empty `pyproject.toml`; `requirements.txt` is the source of truth):

```bash
pip install -r requirements.txt
```

A `.env` file at the repo root is required with at minimum:

```
OPENAI_API_KEY=...
```

Run the full pipeline (interactive — prompts for resume and JD PDF paths):

```bash
python src/main.py
```

Run a single stage in isolation (each stage reads the most recent JSON files produced by the previous stage, so order matters):

```bash
python src/Resume_and_JD_parse.py      # stage 1: PDF → saved_details/resume_*.json + job_description_*.json
python src/job_related_projects.py     # stage 2: job_description_*.json → job_analysis_*.json
python src/resume_generator.py         # stage 3: resume_*.json + job_analysis_*.json → modified_resume/modified_resume.{tex,pdf}
python src/interview_prep.py           # stage 4 (also runnable standalone): job_analysis_*.json → modified_resume/interview_prep.pdf
```

There is no test suite, linter, or build step configured.

## Architecture

The tool is a three-stage LangChain + OpenAI pipeline that turns a resume PDF and a job description PDF into a tailored PDF resume. Stages communicate **only through timestamped JSON files in `saved_details/`** — there is no in-memory handoff between stages even when running via `main.py`. Each stage resolves its inputs with `get_latest_json_file(dir, prefix)`, which picks the newest matching file by mtime/ctime. This means:

- All commands must be run from the repo root so the relative paths `saved_details/` and `modified_resume/` resolve correctly.
- Re-running a stage without cleaning `saved_details/` will pick up whatever is newest, which can silently mix unrelated runs.
- `main.py` still goes through the filesystem between stages and sleeps 1s between them to let files flush.

Stage responsibilities:

1. **`src/Resume_and_JD_parse.py`** — `DocumentParser` class. Extracts text with PyPDF2, splits into 2000-char chunks via `RecursiveCharacterTextSplitter`, then runs a `PydanticOutputParser` chain (`ResumeData` / `JobDescription` schemas) over each chunk. Resume results from all chunks are merged in `merge_resume_data` with per-field deduplication (`_remove_duplicates` keyed on `degree` / `position` / `name`); the JD parse only processes the **first chunk**, so very long JDs can lose tail content.

2. **`src/job_related_projects.py`** — Given the parsed JD, runs **two independent LLM chains**: `generate_project_suggestions` (temperature 0.7, produces 4 fabricated projects aligned with the JD) and `extract_relevant_skills` (temperature 0.2, categorizes skills into technical/soft/tools/domain). Output is `job_analysis_*.json` combining both. Note: the generated projects are hallucinated from the JD, not from the candidate's actual resume.

   **Companion — `src/interview_prep.py`** (stage 4 in the full pipeline; also runnable standalone): reads the latest `job_analysis_*.json` and, for each fabricated project, runs a third LLM chain (`gpt-4.1-mini`, temp 0.4, Pydantic-parsed to `ProjectInterviewPrep`) to produce ≥10 interview Q&A pairs spanning technical / architecture / challenges / impact / behavioral / follow-up categories. Rendered to `modified_resume/interview_prep.pdf` via ReportLab (`render_pdf`). Wired into `main.py` as Step 4 (after `resume_generator`) and also invocable standalone with `python src/interview_prep.py`. The candidate is meant to study the PDF so they can defend the fabricated projects in a real interview.

3. **`src/resume_generator.py`** — Reads the latest `resume_*.json` and `job_analysis_*.json`, combines them in `combine_resume_data`: personal info + education + experience come from the real resume, while **projects and skills are overwritten from `job_analysis`** (the hallucinated ones). Generates a LaTeX document (`build_latex_document`) by reusing the preamble of `src/resumeTemplate.txt` (the Jake Gutierrez template, MIT) and emitting fresh body sections via `render_heading` / `render_education` / `render_experience` / `render_projects` / `render_skills`. The `.tex` is written to `modified_resume/modified_resume.tex` and then compiled to `modified_resume/modified_resume.pdf` by `compile_latex_to_pdf`, which drives a `pylatex.Document` subclass (`_RawDocument`) whose `dumps()` returns the pre-built source verbatim — pylatex owns the subprocess plumbing to `pdflatex`. Both files are overwritten on each run.

## Gotchas

- **Stage 3 needs a system LaTeX install.** `pylatex` only constructs documents and shells out to a real LaTeX engine — it doesn't ship one. `pdflatex` (or `latexmk`) must be on `$PATH`, e.g. `brew install --cask basictex` (slim, ~100 MB) or `mactex-no-gui` (full TeX Live), then `eval "$(/usr/libexec/path_helper)"` in a new shell. `compile_latex_to_pdf` checks for the binary up front and raises a `RuntimeError` with install instructions if it's missing — don't paper over that with a fallback.
- **README still says ReportLab** in its "Technical Details" section; the code now uses LaTeX + pylatex. The README is doc-rot until someone updates it.
- **Model name mismatch with README.** The scripts hardcode `gpt-4o-mini` in `ChatOpenAI(...)` calls; the README still says `gpt-4-turbo-preview`. Treat the code as authoritative and update either side intentionally rather than assuming one was a typo.
- **Pinned `langchain-openai==0.0.2` is very old** and drifts from the newer `langchain>=0.1.0` / `langchain-core>=0.1.10` pins. If you touch imports or chain construction, expect to bump versions together.
- **`requirements.txt` pulls in spacy/nltk/chromadb/jinja2/python-docx** that no source file currently uses. Don't assume those dependencies reflect real features — they don't.
- **`pyproject.toml` declares `requires-python = ">=3.12"`** and lists zero dependencies, while `.python-version` and `requirements.txt` imply the project is actually managed via pip. If you add tooling, reconcile these rather than picking one at random.
- **Resume projects are replaced, not augmented.** Anyone expecting the candidate's real projects to appear in the output PDF will be surprised — only the LLM-generated ones do. This is a deliberate choice of the current pipeline; flag it before "fixing" it.

<!-- code-review-graph MCP tools -->
## MCP Tools: code-review-graph

**IMPORTANT: This project has a knowledge graph. ALWAYS use the
code-review-graph MCP tools BEFORE using Grep/Glob/Read to explore
the codebase.** The graph is faster, cheaper (fewer tokens), and gives
you structural context (callers, dependents, test coverage) that file
scanning cannot.

### When to use graph tools FIRST

- **Exploring code**: `semantic_search_nodes` or `query_graph` instead of Grep
- **Understanding impact**: `get_impact_radius` instead of manually tracing imports
- **Code review**: `detect_changes` + `get_review_context` instead of reading entire files
- **Finding relationships**: `query_graph` with callers_of/callees_of/imports_of/tests_for
- **Architecture questions**: `get_architecture_overview` + `list_communities`

Fall back to Grep/Glob/Read **only** when the graph doesn't cover what you need.

### Key Tools

| Tool | Use when |
|------|----------|
| `detect_changes` | Reviewing code changes — gives risk-scored analysis |
| `get_review_context` | Need source snippets for review — token-efficient |
| `get_impact_radius` | Understanding blast radius of a change |
| `get_affected_flows` | Finding which execution paths are impacted |
| `query_graph` | Tracing callers, callees, imports, tests, dependencies |
| `semantic_search_nodes` | Finding functions/classes by name or keyword |
| `get_architecture_overview` | Understanding high-level codebase structure |
| `refactor_tool` | Planning renames, finding dead code |

### Workflow

1. The graph auto-updates on file changes (via hooks).
2. Use `detect_changes` for code review.
3. Use `get_affected_flows` to understand impact.
4. Use `query_graph` pattern="tests_for" to check coverage.
