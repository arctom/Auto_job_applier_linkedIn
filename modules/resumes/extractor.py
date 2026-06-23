'''
Author:     Tom Arc
LinkedIn:   https://www.linkedin.com/in/tom-arc

Copyright (C) 2024 Tom Arc
'''


import os
import json
import re

from config.questions import default_resume_path
from modules.helpers import print_lg


def extract_text_from_pdf(pdf_path: str) -> str:
    '''
    Extract raw text from a PDF resume using pdfplumber.
    '''
    try:
        import pdfplumber
    except ImportError:
        raise ImportError("pdfplumber is required for PDF parsing. Install it with: pip install pdfplumber")

    text_parts = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n".join(text_parts)


def extract_text_from_docx(docx_path: str) -> str:
    '''
    Extract raw text from a DOCX resume using python-docx.
    '''
    try:
        import docx
    except ImportError:
        raise ImportError("python-docx is required for DOCX parsing. Install it with: pip install python-docx")

    doc = docx.Document(docx_path)
    text_parts = []
    for para in doc.paragraphs:
        if para.text.strip():
            text_parts.append(para.text)
    return "\n".join(text_parts)


def extract_resume_text(resume_path: str) -> str:
    '''
    Auto-detect file type and extract text from PDF or DOCX.
    '''
    ext = os.path.splitext(resume_path)[1].lower()
    if ext == '.pdf':
        return extract_text_from_pdf(resume_path)
    elif ext in ['.docx', '.doc']:
        return extract_text_from_docx(resume_path)
    elif ext == '.txt':
        with open(resume_path, 'r', encoding='utf-8') as f:
            return f.read()
    else:
        raise ValueError(f"Unsupported resume file type: {ext}")


def parse_resume_to_profile(resume_text: str, ai_client, ai_completion_fn) -> dict:
    '''
    Uses LLM to extract structured profile from resume text.
    Returns dict with: skills (list), years_of_experience (int),
    education (list), past_employers (list), job_titles (list),
    certifications (list), summary (str)
    '''
    if not ai_client:
        print_lg("No AI client available for resume parsing. Returning empty profile.")
        return _empty_profile()

    prompt = _resume_parsing_prompt.format(resume_text=resume_text)

    messages = [{"role": "user", "content": prompt}]

    try:
        result = ai_completion_fn(ai_client, messages, response_format=_resume_profile_response_format, stream=False)
        if isinstance(result, dict) and "error" not in result:
            profile = {
                "skills": result.get("skills", []),
                "years_of_experience": result.get("years_of_experience", 0),
                "education": result.get("education", []),
                "past_employers": result.get("past_employers", []),
                "job_titles": result.get("job_titles", []),
                "certifications": result.get("certifications", []),
                "summary": result.get("summary", ""),
                "languages": result.get("languages", []),
            }
            print_lg(f"Parsed resume profile: {len(profile['skills'])} skills, {len(profile['past_employers'])} employers")
            return profile
        else:
            print_lg(f"Failed to parse resume: {result.get('error', 'Unknown error')}")
    except Exception as e:
        print_lg(f"Error parsing resume with AI: {e}")

    return _empty_profile()


def _empty_profile() -> dict:
    return {
        "skills": [],
        "years_of_experience": 0,
        "education": [],
        "past_employers": [],
        "job_titles": [],
        "certifications": [],
        "summary": "",
        "languages": [],
    }


_user_profile_cache = None
_cached_resume_path = None


def get_user_profile(ai_client=None, ai_completion_fn=None, resume_path: str = None) -> dict:
    '''
    Main entry point: extracts resume text, parses it with LLM,
    returns structured user profile dict.
    Caches result to avoid re-parsing on every call.
    '''
    global _user_profile_cache, _cached_resume_path

    if resume_path is None:
        resume_path = default_resume_path

    if _user_profile_cache is not None and _cached_resume_path == resume_path:
        return _user_profile_cache

    try:
        if not os.path.exists(resume_path):
            print_lg(f"Resume not found at {resume_path}, returning empty profile.")
            return _empty_profile()

        resume_text = extract_resume_text(resume_path)
        if not resume_text.strip():
            print_lg("Resume text extraction returned empty result.")
            return _empty_profile()

        print_lg(f"Extracted {len(resume_text)} characters from resume.")

        if ai_client and ai_completion_fn:
            profile = parse_resume_to_profile(resume_text, ai_client, ai_completion_fn)
        else:
            print_lg("No AI client provided, using basic regex extraction from resume.")
            profile = _basic_regex_extraction(resume_text)
    except Exception as e:
        print_lg(f"Failed to get user profile: {e}")
        profile = _empty_profile()

    _user_profile_cache = profile
    _cached_resume_path = resume_path
    return profile


def _basic_regex_extraction(text: str) -> dict:
    '''
    Fallback: basic regex-based extraction when AI is not available.
    '''
    skills = []
    skill_keywords = [
        "Python", "Java", "JavaScript", "TypeScript", "C\\+\\+", "Go", "Rust", "Ruby", "PHP",
        "React", "Angular", "Vue", "Node\\.js", "Django", "Flask", "FastAPI", "Spring",
        "TensorFlow", "PyTorch", "Keras", "scikit-learn", "Pandas", "NumPy",
        "SQL", "MongoDB", "PostgreSQL", "MySQL", "Redis", "Elasticsearch",
        "AWS", "GCP", "Azure", "Docker", "Kubernetes", "Terraform", "CI/CD",
        "Git", "Linux", "Agile", "Scrum", "REST", "GraphQL", "gRPC",
        "NLP", "Computer Vision", "ML", "AI", "Deep Learning",
    ]
    for kw in skill_keywords:
        if re.search(r'\b' + kw + r'\b', text, re.IGNORECASE):
            skills.append(kw.replace("\\", ""))

    years_exp = 0
    exp_patterns = [
        r'(\d+)\+?\s*years?\s*(?:of\s*)?experience',
        r'experience\s*(?:of\s*)?(\d+)\+?\s*years?',
        r'(\d+)\s*\+\s*years?',
    ]
    for pattern in exp_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            years_exp = max(int(m) for m in matches if int(m) <= 50)
            break

    return {
        "skills": list(set(skills)),
        "years_of_experience": years_exp,
        "education": [],
        "past_employers": [],
        "job_titles": [],
        "certifications": [],
        "summary": text[:500] if text else "",
        "languages": [],
    }


_resume_parsing_prompt = """
You are a resume parser. Extract structured information from the resume text below.
Be accurate and truthful. If information is not found, leave the field empty.

RESUME TEXT:
{resume_text}

Return a JSON object with the following fields:
- skills: list of technical and soft skills mentioned
- years_of_experience: total years of professional experience as an integer
- education: list of education entries (degree, institution)
- past_employers: list of previous company names
- job_titles: list of previous job titles
- certifications: list of certifications
- summary: a 2-3 sentence professional summary
- languages: list of languages the person knows

Return ONLY valid JSON with no additional commentary.
"""

_resume_profile_response_format = {"type": "json_object"}
