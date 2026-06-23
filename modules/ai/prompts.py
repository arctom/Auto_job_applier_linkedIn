"""
Author:     Sai Vignesh Golla
LinkedIn:   https://www.linkedin.com/in/saivigneshgolla/

Copyright (C) 2024 Sai Vignesh Golla

License:    GNU Affero General Public License
            https://www.gnu.org/licenses/agpl-3.0.en.html
            
GitHub:     https://github.com/GodsScion/Auto_job_applier_linkedIn

version:    24.12.29.12.30
"""


##> Extract Skills

# Structure of messages = `[{"role": "user", "content": extract_skills_prompt}]`

extract_skills_prompt = """
You are a job requirements extractor and classifier. Your task is to extract all skills mentioned in a job description and classify them into five categories:
1. "tech_stack": Identify all skills related to programming languages, frameworks, libraries, databases, and other technologies used in software development. Examples include Python, React.js, Node.js, Elasticsearch, Algolia, MongoDB, Spring Boot, .NET, etc.
2. "technical_skills": Capture skills related to technical expertise beyond specific tools, such as architectural design or specialized fields within engineering. Examples include System Architecture, Data Engineering, System Design, Microservices, Distributed Systems, etc.
3. "other_skills": Include non-technical skills like interpersonal, leadership, and teamwork abilities. Examples include Communication skills, Managerial roles, Cross-team collaboration, etc.
4. "required_skills": All skills specifically listed as required or expected from an ideal candidate. Include both technical and non-technical skills.
5. "nice_to_have": Any skills or qualifications listed as preferred or beneficial for the role but not mandatory.
Return the output in the following JSON format with no additional commentary:
{{
    "tech_stack": [],
    "technical_skills": [],
    "other_skills": [],
    "required_skills": [],
    "nice_to_have": []
}}

JOB DESCRIPTION:
{}
"""
"""
Use `extract_skills_prompt.format(job_description)` to insert `job_description`.
"""


extract_skills_response_format = {"type": "json_object"}
"""
Response schema for `extract_skills` function
"""
#<


##> Answer Questions
# Structure of messages = `[{"role": "user", "content": answer_questions_prompt}]`

text_questions_prompt = """
Please answer the following job application question, with no additional commentary, based on the context provided.
Question:
{}
User Info:
{}
"""
#<


##> Answer Question with Context (Phase 2.2)
answer_question_prompt = """
You are answering job application questions on behalf of the user. Answer truthfully based on the user's profile. Never invent qualifications the user doesn't have.

USER PROFILE:
{user_profile}

SKILL YEARS OF EXPERIENCE:
{skill_years}
(If asked about a technology not listed above, infer from the most similar technology the user knows. Always use these exact years when asked.)

JOB DESCRIPTION (for context):
{job_description}

QUESTION TYPE: {question_type}
QUESTION: {question}

AVAILABLE OPTIONS: {options}

Return ONLY the answer text (or selected option), with no additional commentary.
For single_select and multiple_select questions, you MUST return EXACTLY one of the available options as written — match the text precisely, including language and capitalization. If the options are in Spanish, answer in Spanish. If in French, answer in French. Always match the language of the options provided.
IMPORTANT: When the question asks for years of experience, return ONLY the integer (e.g. "3"). Do NOT include "years" or any other text — the field only accepts numbers. If the user has no experience with the technology, answer "0". Never reply with a sentence like "I don't have experience" — always just the number.
"""
#<


##> Cover Letter Generation (Phase 2.3)
cover_letter_prompt = """
You are a professional cover letter writer. Write a concise, tailored cover letter for a job application. The letter should:
- Be under 1500 characters
- Address the company by name
- Reference 2-3 specific requirements from the job description
- Highlight relevant experience from the user's profile
- Use a professional but warm tone
- Include a call to action at the end

COMPANY: {company_name}
JOB DESCRIPTION: {job_description}
REQUIRED SKILLS: {required_skills}
USER PROFILE: {user_profile}

Return ONLY the cover letter text, no additional commentary.
"""
#<


##> Job Relevance Check (Phase 2.4)
job_relevance_prompt = """
You are a job fit evaluator. Rate how well the user's profile matches the job description on a scale of 0-100. Consider:
- Skill match (technical and soft skills)
- Experience level match
- Domain/industry match
- Any deal-breaker requirements the user doesn't meet

JOB TITLE: {job_title}
COMPANY: {company_name}
JOB DESCRIPTION: {job_description}
USER PROFILE: {user_profile}

Return JSON:
{{"relevance_score": <0-100>, "reasoning": "<2-3 sentences>", "deal_breakers": ["<item>", ...]}}
"""

job_relevance_response_format = {"type": "json_object"}
#<


##> Experience Extraction (Phase 2.5)
experience_extraction_prompt = """
Extract the years of experience required from the job description below. Be precise:
- Look for phrases like "X+ years", "X-Y years", "minimum X years", "at least X years"
- If a range is given (e.g. "5-7 years"), return the maximum
- If no experience requirement is mentioned, return 0
- If the role is explicitly for fresh graduates or entry level, return 0

JOB DESCRIPTION:
{job_description}

Return JSON:
{{"years_required": <integer>, "is_entry_level": <true/false>, "seniority": "<junior/mid/senior/lead/unknown>", "explanation": "<1 sentence>"}}
"""

experience_extraction_response_format = {"type": "json_object"}
#<