import os
import json
import re
import requests
from django.conf import settings


OPENAI_API_KEY = getattr(settings, 'OPENAI_API_KEY', os.environ.get('OPENAI_API_KEY', ''))
IS_VERCEL = os.environ.get('VERCEL', '') == '1'


def _call_openai(prompt, system_prompt, max_tokens=1500, temperature=0.7):
    if not OPENAI_API_KEY:
        return None
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        text = response.choices[0].message.content or ""
        return _strip_markdown(text.strip())
    except Exception as e:
        print(f"[OpenAI Error] {e}")
        return None


def _call_ollama(prompt, system_prompt, max_tokens=1500, temperature=0.7):
    if IS_VERCEL:
        return None
    base_url = getattr(settings, 'OLLAMA_BASE_URL', 'http://localhost:11434')
    model = getattr(settings, 'OLLAMA_MODEL', 'qwen2.5:1.5b')
    try:
        r = requests.get(f"{base_url}/api/tags", timeout=3)
        if r.status_code != 200:
            return None
    except Exception:
        return None
    try:
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
            "system": system_prompt,
        }
        r = requests.post(f"{base_url}/api/generate", json=payload, timeout=30)
        if r.status_code == 200:
            response = r.json().get("response", "")
            return _strip_markdown(response.strip()) if response.strip() else None
    except Exception:
        pass
    return None


def generate_with_ai(prompt, max_tokens=1500, temperature=0.7):
    system_prompt = (
        "You are an expert HR professional, career coach, and resume analyst. "
        "Give clear, detailed, and actionable answers. "
        "Write plain text for cover letters. "
        "Return only valid JSON (no markdown code blocks) when asked for JSON. "
        "Personalize all responses based on the candidate's actual resume data."
    )

    result = _call_openai(prompt, system_prompt, max_tokens, temperature)
    if result:
        return result

    result = _call_ollama(prompt, system_prompt, max_tokens, temperature)
    if result:
        return result

    return generate_fallback(prompt)


def _strip_markdown(text):
    if not text:
        return text
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'`(.+?)`', r'\1', text)
    text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
    return text.strip()


def _try_parse_json(text):
    if not text:
        return None
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        pass
    match = re.search(r'[\[\{].*[\]\}]', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except (json.JSONDecodeError, TypeError):
            pass
    return None


def generate_fallback(prompt):
    prompt_lower = prompt.lower()
    if 'cover letter' in prompt_lower:
        return generate_cover_letter_fallback(prompt)
    elif 'interview question' in prompt_lower:
        return generate_interview_questions_fallback(prompt)
    elif 'improve' in prompt_lower or 'suggestion' in prompt_lower:
        return generate_improvement_fallback(prompt)
    elif 'skill gap' in prompt_lower:
        return generate_skill_gap_fallback(prompt)
    elif 'job match' in prompt_lower or 'recommend' in prompt_lower:
        return generate_job_match_fallback(prompt)
    elif 'candidate rank' in prompt_lower or 'match score' in prompt_lower:
        return generate_candidate_match_fallback(prompt)
    return "AI analysis complete. Please review the results below."


def generate_cover_letter(resume_data, company, role, job_description=""):
    skills = ', '.join(resume_data.get('skills', [])[:10])
    experience = resume_data.get('experience', [])
    summary = resume_data.get('summary', 'N/A')
    education = resume_data.get('education', [])
    candidate_name = resume_data.get('name', 'Candidate')

    exp_text = ""
    if experience:
        for exp in experience[:3]:
            if isinstance(exp, dict):
                exp_text += f"- {exp.get('title', '')} at {exp.get('company', '')} ({exp.get('duration', '')})\n"
            else:
                exp_text += f"- {exp}\n"

    edu_text = ""
    if education:
        for edu in education[:2]:
            if isinstance(edu, dict):
                edu_text += f"- {edu.get('degree', '')} from {edu.get('institution', '')}\n"
            else:
                edu_text += f"- {edu}\n"

    prompt = f"""Write a professional cover letter for a {role} position at {company}.

Candidate Profile:
- Name: {candidate_name}
- Skills: {skills}
- Summary: {summary}
- Experience:
{exp_text if exp_text else 'Fresh graduate, no formal work experience yet.'}
- Education:
{edu_text if edu_text else 'N/A'}
{f'- Job Description: {job_description[:500]}' if job_description else ''}

Requirements:
1. Start with "Dear Hiring Manager,"
2. Write exactly 4 paragraphs: opening, skills match, experience/education fit, closing
3. Reference the candidate's ACTUAL skills and projects from their resume
4. Be specific about how their skills match the {role} role
5. End with "Sincerely," followed by the candidate's name ({candidate_name})
6. Keep it under 300 words, professional tone"""

    return generate_with_ai(prompt, max_tokens=800, temperature=0.7)


def generate_interview_questions(resume_data, skills=None):
    if not skills:
        skills = resume_data.get('skills', [])[:6]
    skills_text = ', '.join(skills)

    prompt = f"""Generate 12 interview questions for a candidate with these skills: {skills_text}

Create questions that are SPECIFIC to each skill the candidate has listed. Do NOT generate generic questions.

For each skill, generate:
- 1 easy question (fundamentals)
- 1 medium question (intermediate concepts)
- 1 hard question (advanced/system design) where applicable

Also include 2-3 behavioral questions relevant to a tech role.

Return as a JSON array. Each object must have exactly these fields:
- "skill": the skill name (e.g., "Python", "Django")
- "question": the full interview question
- "difficulty": one of "easy", "medium", "hard"
- "category": one of "technical" or "behavioral"

Return ONLY the JSON array, no markdown, no extra text."""

    response = generate_with_ai(prompt, max_tokens=1500, temperature=0.8)
    parsed = _try_parse_json(response)
    if isinstance(parsed, list) and len(parsed) > 0:
        return parsed
    return json.loads(generate_interview_questions_fallback(""))


def generate_improvements(resume_data, raw_text):
    skills = ', '.join(resume_data.get('skills', []))
    experience = resume_data.get('experience', [])
    summary = resume_data.get('summary', 'N/A')

    exp_text = ""
    if experience:
        for exp in experience[:3]:
            if isinstance(exp, dict):
                exp_text += f"{json.dumps(exp)}\n"
            else:
                exp_text += f"{exp}\n"

    prompt = f"""Analyze this resume and suggest specific, actionable improvements.

Resume Content:
Skills: {skills}
Summary: {summary}
Experience: {exp_text if exp_text else 'No experience listed'}
Full Text: {raw_text[:2000] if raw_text else 'N/A'}

Provide 4-5 improvements covering different sections. For each improvement:
1. Identify the EXACT section that needs improvement
2. Show the ORIGINAL text as it appears in the resume (or a placeholder if missing)
3. Write an IMPROVED version that is specific to THIS candidate's background
4. Explain WHY the improvement matters

Return as JSON with this exact structure:
{{"improvements": [{{"section": "Section Name", "original": "current text", "improved": "better version", "explanation": "why this helps"}}]}}

Return ONLY valid JSON, no markdown."""

    response = generate_with_ai(prompt, max_tokens=1500, temperature=0.7)
    parsed = _try_parse_json(response)
    if isinstance(parsed, dict) and 'improvements' in parsed:
        return parsed
    if isinstance(parsed, list):
        return {'improvements': parsed}
    return json.loads(generate_improvement_fallback(""))


def analyze_skill_gap(resume_data, target_role):
    current_skills = ', '.join(resume_data.get('skills', []))
    experience = resume_data.get('experience', [])

    prompt = f"""Analyze the skill gap for a candidate wanting to become a {target_role}.

Candidate's Current Skills: {current_skills}
Work Experience: {len(experience)} positions

Provide:
1. Missing skills needed for {target_role} - list each with importance (high/medium/low) and category
2. Specific learning recommendations for each missing skill
3. A phased learning roadmap with concrete steps

Return as JSON with this exact structure:
{{
  "missing_skills": [{{"skill": "Skill Name", "importance": "high/medium/low", "category": "Category"}}],
  "recommendations": ["recommendation 1", "recommendation 2", ...],
  "learning_roadmap": [
    {{"phase": "Beginner", "skills": ["skill1", "skill2"]}},
    {{"phase": "Intermediate", "skills": ["skill3", "skill4"]}},
    {{"phase": "Advanced", "skills": ["skill5", "skill6"]}}
  ]
}}

Return ONLY valid JSON, no markdown."""

    response = generate_with_ai(prompt, max_tokens=1200, temperature=0.7)
    parsed = _try_parse_json(response)
    if isinstance(parsed, dict):
        return parsed
    return json.loads(generate_skill_gap_fallback(""))


def match_jobs(resume_data, jobs):
    skills = set(s.lower() for s in resume_data.get('skills', []))
    recommendations = []
    for job in jobs:
        job_skills = set(s.lower() for s in (job.required_skills or []))
        preferred = set(s.lower() for s in (job.preferred_skills or []))
        if not job_skills:
            score = 50
        else:
            required_match = len(skills.intersection(job_skills)) / max(len(job_skills), 1)
            preferred_match = len(skills.intersection(preferred)) / max(len(preferred), 1) * 0.3
            score = min((required_match * 0.7 + preferred_match) * 100, 100)
        matching = list(skills.intersection(job_skills.union(preferred)))
        missing = list(job_skills - skills)
        recommendations.append({
            'job': job,
            'match_score': round(score, 1),
            'matching_skills': matching,
            'missing_skills': missing,
        })
    recommendations.sort(key=lambda x: x['match_score'], reverse=True)
    return recommendations


def rank_candidates(candidates_data, job):
    job_skills = set(s.lower() for s in (job.required_skills or []))
    ranked = []
    for data in candidates_data:
        candidate_skills = set(s.lower() for s in data.get('skills', []))
        ats_score = data.get('ats_score', 0)
        if job_skills:
            skill_match = len(candidate_skills.intersection(job_skills)) / max(len(job_skills), 1)
        else:
            skill_match = 0.5
        match_score = (skill_match * 60 + (ats_score / 100) * 40)
        ranked.append({
            'candidate': data.get('user'),
            'ats_score': ats_score,
            'match_score': round(match_score, 1),
            'matching_skills': list(candidate_skills.intersection(job_skills)),
        })
    ranked.sort(key=lambda x: x['match_score'], reverse=True)
    return ranked


def generate_cover_letter_fallback(prompt):
    return """Dear Hiring Manager,

I am writing to express my strong interest in the position at your esteemed organization. With my background in software development and passion for creating impactful solutions, I believe I would be a valuable addition to your team.

Throughout my career, I have developed expertise in building scalable applications, working with modern technologies, and collaborating effectively with cross-functional teams. My technical skills, combined with my problem-solving abilities, enable me to deliver high-quality results consistently.

I am excited about the opportunity to contribute to your organization's success and would welcome the chance to discuss how my skills and experience align with your needs. Thank you for considering my application.

Sincerely,
[Your Name]"""


def generate_interview_questions_fallback(prompt):
    questions = [
        {"skill": "Python", "question": "Explain the difference between a list and a tuple in Python.", "difficulty": "easy", "category": "technical"},
        {"skill": "Django", "question": "Explain Django's MVT (Model-View-Template) architecture.", "difficulty": "medium", "category": "technical"},
        {"skill": "SQL", "question": "What are the different types of SQL JOINs? Explain with examples.", "difficulty": "medium", "category": "technical"},
        {"skill": "REST API", "question": "What are REST APIs? Explain the difference between GET, POST, PUT, and DELETE.", "difficulty": "easy", "category": "technical"},
        {"skill": "Docker", "question": "What is Docker? Explain the difference between a Docker image and a container.", "difficulty": "medium", "category": "technical"},
        {"skill": "General", "question": "Tell me about a challenging project you worked on and how you overcame the difficulties.", "difficulty": "medium", "category": "behavioral"},
        {"skill": "General", "question": "How do you stay updated with the latest technologies?", "difficulty": "easy", "category": "behavioral"},
        {"skill": "General", "question": "Describe your experience with agile/scrum development methodologies.", "difficulty": "medium", "category": "behavioral"},
        {"skill": "Python", "question": "What is the difference between Django ORM and raw SQL? When would you use each?", "difficulty": "hard", "category": "technical"},
        {"skill": "General", "question": "How do you handle code reviews and feedback from peers?", "difficulty": "easy", "category": "behavioral"},
    ]
    return json.dumps(questions)


def generate_improvement_fallback(prompt):
    return json.dumps({
        "improvements": [
            {
                "section": "Summary",
                "original": "Looking for a job in software development.",
                "improved": "Results-driven software developer with 3+ years of experience in building scalable web applications using Python, Django, and modern front-end technologies. Passionate about writing clean, maintainable code and delivering impactful user experiences.",
                "explanation": "Made the summary more specific, added quantifiable experience, and highlighted key technologies."
            },
            {
                "section": "Experience",
                "original": "Worked on Django project.",
                "improved": "Developed and maintained a scalable Django-based web application serving 10,000+ daily users, implementing RESTful APIs, PostgreSQL database optimization, and JWT authentication, resulting in a 40% improvement in API response times.",
                "explanation": "Added specific metrics, technologies used, and measurable impact."
            },
            {
                "section": "Skills",
                "original": "Python, HTML, CSS",
                "improved": "Python, Django, REST APIs, PostgreSQL, HTML5, CSS3, JavaScript, Git, Docker, AWS, CI/CD, Agile/Scrum",
                "explanation": "Expanded the skills list with relevant technologies that are commonly sought by employers."
            }
        ]
    })


def generate_skill_gap_fallback(prompt):
    return json.dumps({
        "missing_skills": [
            {"skill": "Docker", "importance": "high", "category": "DevOps"},
            {"skill": "REST API Design", "importance": "high", "category": "Backend"},
            {"skill": "AWS", "importance": "medium", "category": "Cloud"},
            {"skill": "Redis", "importance": "medium", "category": "Database"},
            {"skill": "Celery", "importance": "medium", "category": "Backend"},
            {"skill": "pytest", "importance": "high", "category": "Testing"},
            {"skill": "CI/CD", "importance": "medium", "category": "DevOps"},
        ],
        "recommendations": [
            "Start with Docker basics - it's essential for modern development workflows.",
            "Learn REST API design principles and best practices.",
            "Get familiar with at least one cloud platform (AWS recommended).",
            "Understand caching with Redis for performance optimization.",
            "Learn unit testing with pytest for better code quality.",
        ],
        "learning_roadmap": [
            {"phase": "Beginner", "skills": ["Docker Basics", "REST API Fundamentals", "Git Advanced"]},
            {"phase": "Intermediate", "skills": ["AWS Core Services", "Redis", "Celery", "pytest"]},
            {"phase": "Advanced", "skills": ["Kubernetes", "CI/CD Pipelines", "Microservices", "System Design"]}
        ]
    })


def generate_job_match_fallback(prompt):
    return json.dumps([
        {"title": "Python Developer", "match_score": 95, "company": "Tech Corp"},
        {"title": "Backend Developer", "match_score": 90, "company": "InnovateTech"},
        {"title": "Django Developer", "match_score": 89, "company": "WebSolutions"},
        {"title": "Full Stack Developer", "match_score": 82, "company": "DigitalAgency"},
        {"title": "Software Engineer", "match_score": 80, "company": "StartupXYZ"},
    ])


def generate_candidate_match_fallback(prompt):
    return json.dumps({
        "match_score": 85,
        "matching_skills": ["Python", "Django", "SQL", "Git"],
        "missing_skills": ["Docker", "AWS", "Redis"],
        "strengths": ["Strong Python experience", "Good educational background"],
        "weaknesses": ["Limited cloud experience", "No DevOps experience"],
        "recommendation": "Strong candidate with solid fundamentals. Recommend for interview with focus on cloud/DevOps growth potential."
    })
