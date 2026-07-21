import os
import json
import requests
from django.conf import settings


def get_ollama_config():
    base_url = getattr(settings, 'OLLAMA_BASE_URL', 'http://localhost:11434')
    model = getattr(settings, 'OLLAMA_MODEL', 'qwen2.5:1.5b')
    return base_url, model


def is_ollama_available():
    base_url, _ = get_ollama_config()
    try:
        r = requests.get(f"{base_url}/api/tags", timeout=5)
        return r.status_code == 200
    except Exception:
        return False


def get_installed_models():
    base_url, _ = get_ollama_config()
    try:
        r = requests.get(f"{base_url}/api/tags", timeout=5)
        if r.status_code == 200:
            data = r.json()
            return [m['name'] for m in data.get('models', [])]
    except Exception:
        pass
    return []


def generate_with_ai(prompt, max_tokens=1500, temperature=0.7):
    base_url, model = get_ollama_config()

    if not is_ollama_available():
        return generate_fallback(prompt)

    try:
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
            "system": "You are an expert HR professional and career coach. Give clear, helpful answers. Write plain text for cover letters. Return only valid JSON (no markdown) when asked for JSON.",
        }
        r = requests.post(f"{base_url}/api/generate", json=payload, timeout=180)
        if r.status_code == 200:
            response = r.json().get("response", "")
            response = _strip_markdown(response)
            return response if response.strip() else generate_fallback(prompt)
        return generate_fallback(prompt)
    except Exception:
        return generate_fallback(prompt)


def _strip_markdown(text):
    if not text:
        return text
    import re
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


def generate_cover_letter_prompt(company, role, resume_data, job_description=""):
    skills = ', '.join(resume_data.get('skills', [])[:8])

    return f"""Write a 3 paragraph cover letter for a {role} position at {company}.
Candidate skills: {skills}
Summary: {resume_data.get('summary', 'N/A')[:150]}

Write it as a professional letter starting with Dear Hiring Manager and ending with Sincerely.
Make it concise and tailored to the role."""


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


def generate_cover_letter(resume_data, company, role, job_description=""):
    prompt = generate_cover_letter_prompt(company, role, resume_data, job_description)
    return generate_with_ai(prompt, max_tokens=800)


def generate_interview_questions(resume_data, skills=None):
    if not skills:
        skills = resume_data.get('skills', [])[:5]
    skills_text = ', '.join(skills)

    prompt = f"""Generate 10 interview questions for a candidate with these skills: {skills_text}

Include a mix of:
- Technical questions for each skill
- Behavioral questions
- Problem-solving questions

Return as JSON array with fields: skill, question, difficulty (easy/medium/hard), category (technical/behavioral)
Return ONLY valid JSON, no markdown."""

    response = generate_with_ai(prompt, max_tokens=1000)
    try:
        return json.loads(response)
    except (json.JSONDecodeError, TypeError):
        return json.loads(generate_interview_questions_fallback(""))


def generate_improvements(resume_data, raw_text):
    prompt = f"""Analyze this resume and suggest improvements:

Skills: {', '.join(resume_data.get('skills', []))}
Summary: {resume_data.get('summary', 'N/A')}
Experience: {resume_data.get('experience', [])}

Suggest improvements for each section with original text and improved version.
Return as JSON with field "improvements" containing objects with: section, original, improved, explanation.
Return ONLY valid JSON, no markdown."""

    response = generate_with_ai(prompt, max_tokens=1500)
    try:
        return json.loads(response)
    except (json.JSONDecodeError, TypeError):
        return json.loads(generate_improvement_fallback(""))


def analyze_skill_gap(resume_data, target_role):
    current_skills = ', '.join(resume_data.get('skills', []))

    prompt = f"""Analyze skill gap for a candidate wanting to become a {target_role}.

Current Skills: {current_skills}
Experience: {len(resume_data.get('experience', []))} positions

Provide:
1. Missing skills needed for the target role (with importance level)
2. Learning recommendations
3. A phased learning roadmap (beginner, intermediate, advanced)

Return as JSON with fields: missing_skills, recommendations, learning_roadmap.
Return ONLY valid JSON, no markdown."""

    response = generate_with_ai(prompt, max_tokens=1200)
    try:
        return json.loads(response)
    except (json.JSONDecodeError, TypeError):
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
