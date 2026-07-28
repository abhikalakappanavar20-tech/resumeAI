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
        r = requests.post(f"{base_url}/api/generate", json=payload, timeout=60)
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

    return None


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


def is_ai_available():
    return bool(OPENAI_API_KEY)


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

    result = generate_with_ai(prompt, max_tokens=800, temperature=0.7)
    if result:
        return result

    return f"""Dear Hiring Manager,

I am writing to express my strong interest in the {role} position at {company}. With my background in {skills[:100] if skills else 'software development'} and passion for creating impactful solutions, I believe I would be a valuable addition to your team.

Throughout my career, I have developed expertise in building scalable applications, working with modern technologies, and collaborating effectively with cross-functional teams. My technical skills, combined with my problem-solving abilities, enable me to deliver high-quality results consistently.

{f"I am excited about the opportunity to contribute to {company}'s success" if company else 'I am excited about the opportunity to contribute to your organization\'s success'} and would welcome the chance to discuss how my skills and experience align with your needs. Thank you for considering my application.

Sincerely,
{candidate_name}"""


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

    return [
        {"skill": skills[0] if skills else "Python", "question": f"Explain the core concepts and best practices of {skills[0] if skills else 'Python'}.", "difficulty": "easy", "category": "technical"},
        {"skill": skills[0] if skills else "Python", "question": f"Describe a complex project where you used {skills[0] if skills else 'Python'}. What challenges did you face?", "difficulty": "medium", "category": "technical"},
        {"skill": skills[1] if len(skills) > 1 else "General", "question": f"How do you approach debugging and testing in {skills[1] if len(skills) > 1 else 'your development workflow'}?", "difficulty": "medium", "category": "technical"},
        {"skill": "General", "question": "Tell me about a challenging project you worked on and how you overcame the difficulties.", "difficulty": "medium", "category": "behavioral"},
        {"skill": "General", "question": "How do you stay updated with the latest technologies?", "difficulty": "easy", "category": "behavioral"},
    ]


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

    return {
        "improvements": [
            {
                "section": "Summary",
                "original": summary if summary != 'N/A' else "Professional seeking new opportunities.",
                "improved": f"Results-driven professional with expertise in {skills[:100] if skills else 'software development'}, passionate about delivering high-quality solutions and driving innovation.",
                "explanation": "Made the summary more specific, added quantifiable experience, and highlighted key technologies."
            },
            {
                "section": "Experience",
                "original": exp_text.strip() if exp_text else "No experience listed",
                "improved": "Developed and maintained scalable web applications using modern technologies, implementing RESTful APIs, database optimization, and best practices, resulting in significant performance improvements.",
                "explanation": "Added specific metrics, technologies used, and measurable impact."
            },
            {
                "section": "Skills",
                "original": skills if skills else "Add your skills",
                "improved": f"{skills}, REST APIs, Git, Docker, CI/CD, Agile/Scrum" if skills else "Python, Django, REST APIs, Git, Docker, CI/CD",
                "explanation": "Expanded the skills list with relevant technologies that are commonly sought by employers."
            }
        ]
    }


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

    return {
        "missing_skills": [
            {"skill": "Cloud Platforms (AWS/GCP/Azure)", "importance": "high", "category": "Cloud"},
            {"skill": "Docker & Kubernetes", "importance": "high", "category": "DevOps"},
            {"skill": "CI/CD Pipelines", "importance": "medium", "category": "DevOps"},
            {"skill": "System Design", "importance": "high", "category": "Architecture"},
            {"skill": "Testing Frameworks", "importance": "medium", "category": "Quality"},
        ],
        "recommendations": [
            f"Focus on cloud platforms - essential for modern {target_role} roles.",
            "Learn containerization with Docker and orchestration with Kubernetes.",
            "Build projects that demonstrate system design thinking.",
            "Practice with testing frameworks relevant to your tech stack.",
        ],
        "learning_roadmap": [
            {"phase": "Beginner", "skills": ["Cloud Fundamentals", "Docker Basics"]},
            {"phase": "Intermediate", "skills": ["Kubernetes", "CI/CD", "System Design"]},
            {"phase": "Advanced", "skills": ["Microservices", "Infrastructure as Code", "Monitoring"]}
        ]
    }


def match_jobs(resume_data, jobs):
    skills = resume_data.get('skills', [])
    experience = resume_data.get('experience', [])
    summary = resume_data.get('summary', '')
    skills_text = ', '.join(skills[:15])

    jobs_context = ""
    for job in jobs[:20]:
        req_skills = ', '.join(job.required_skills or [])
        pref_skills = ', '.join(job.preferred_skills or [])
        jobs_context += f"""
- Job ID: {job.id}, Title: {job.title} at {job.company_name}
  Required Skills: {req_skills}
  Preferred Skills: {pref_skills}
  Description: {(job.description or '')[:200]}
  Experience: {job.experience_required}
  Type: {job.job_type}
"""

    prompt = f"""You are an expert career matching AI. Analyze the candidate and match them against these job listings.

Candidate Profile:
- Skills: {skills_text}
- Experience: {len(experience)} positions
- Summary: {summary[:300] if summary else 'N/A'}

Available Jobs:
{jobs_context}

For EACH job, provide:
1. A match_score (0-100) based on how well the candidate fits
2. A list of matching_skills (skills the candidate has that match the job)
3. A list of missing_skills (skills the job requires but candidate lacks)
4. A brief reason for the score

Return as a JSON array of objects with these fields:
- "job_id": the job ID (UUID string)
- "match_score": number 0-100
- "matching_skills": array of skill strings
- "missing_skills": array of skill strings
- "reason": brief explanation string

Return ONLY the JSON array, sorted by match_score descending."""

    response = generate_with_ai(prompt, max_tokens=2000, temperature=0.3)
    parsed = _try_parse_json(response)

    recommendations = []
    job_map = {str(job.id): job for job in jobs}

    if isinstance(parsed, list):
        for item in parsed:
            job_id = item.get('job_id', '')
            job = job_map.get(job_id)
            if not job:
                continue
            recommendations.append({
                'job': job,
                'match_score': min(max(item.get('match_score', 0), 0), 100),
                'matching_skills': item.get('matching_skills', []),
                'missing_skills': item.get('missing_skills', []),
                'reason': item.get('reason', ''),
            })

    if recommendations:
        recommendations.sort(key=lambda x: x['match_score'], reverse=True)
        return recommendations

    skills_set = set(s.lower() for s in skills)
    for job in jobs:
        job_skills = set(s.lower() for s in (job.required_skills or []))
        preferred = set(s.lower() for s in (job.preferred_skills or []))
        if not job_skills:
            score = 50
        else:
            required_match = len(skills_set.intersection(job_skills)) / max(len(job_skills), 1)
            preferred_match = len(skills_set.intersection(preferred)) / max(len(preferred), 1) * 0.3
            score = min((required_match * 0.7 + preferred_match) * 100, 100)
        matching = list(skills_set.intersection(job_skills.union(preferred)))
        missing = list(job_skills - skills_set)
        recommendations.append({
            'job': job,
            'match_score': round(score, 1),
            'matching_skills': matching,
            'missing_skills': missing,
            'reason': '',
        })
    recommendations.sort(key=lambda x: x['match_score'], reverse=True)
    return recommendations


def rank_candidates(candidates_data, job):
    job_skills = ', '.join(job.required_skills or [])
    job_desc = (job.description or '')[:300]

    candidates_context = ""
    for i, data in enumerate(candidates_data):
        c_skills = ', '.join(data.get('skills', []))
        candidates_context += f"""
- Candidate #{i+1} (ID: {i+1})
  Skills: {c_skills}
  ATS Score: {data.get('ats_score', 0)}
  Summary: {(data.get('summary', '') or '')[:150]}
"""

    prompt = f"""You are an expert recruiter AI. Rank these candidates for a job position.

Job: {job.title} at {job.company_name}
Required Skills: {job_skills}
Description: {job_desc}
Experience Required: {job.experience_required}

Candidates:
{candidates_context}

For EACH candidate, provide:
1. A match_score (0-100) based on fit for this specific role
2. A list of matching_skills
3. A brief strengths assessment
4. A brief weakness or gap

Return as a JSON array sorted by match_score (highest first). Each object:
- "candidate_index": number (1-based index matching the candidate order above)
- "match_score": number 0-100
- "matching_skills": array of strings
- "strengths": brief string
- "weakness": brief string
- "recommendation": "strong_fit" / "good_fit" / "moderate_fit" / "weak_fit"

Return ONLY the JSON array."""

    response = generate_with_ai(prompt, max_tokens=2000, temperature=0.3)
    parsed = _try_parse_json(response)

    ranked = []
    if isinstance(parsed, list):
        for item in parsed:
            idx = item.get('candidate_index', 1) - 1
            if 0 <= idx < len(candidates_data):
                data = candidates_data[idx]
                ranked.append({
                    'candidate': data.get('user'),
                    'ats_score': data.get('ats_score', 0),
                    'match_score': min(max(item.get('match_score', 0), 0), 100),
                    'matching_skills': item.get('matching_skills', []),
                    'strengths': item.get('strengths', ''),
                    'weakness': item.get('weakness', ''),
                    'recommendation': item.get('recommendation', 'moderate_fit'),
                })

    if ranked:
        ranked.sort(key=lambda x: x['match_score'], reverse=True)
        return ranked

    job_skills_set = set(s.lower() for s in (job.required_skills or []))
    for data in candidates_data:
        candidate_skills = set(s.lower() for s in data.get('skills', []))
        ats_score = data.get('ats_score', 0)
        if job_skills_set:
            skill_match = len(candidate_skills.intersection(job_skills_set)) / max(len(job_skills_set), 1)
        else:
            skill_match = 0.5
        match_score = (skill_match * 60 + (ats_score / 100) * 40)
        ranked.append({
            'candidate': data.get('user'),
            'ats_score': ats_score,
            'match_score': round(match_score, 1),
            'matching_skills': list(candidate_skills.intersection(job_skills_set)),
            'strengths': '',
            'weakness': '',
            'recommendation': 'moderate_fit',
        })
    ranked.sort(key=lambda x: x['match_score'], reverse=True)
    return ranked
