import re
import json


def calculate_ats_score(extracted_data, target_job_description="", raw_text=""):
    """Calculate ATS score. AI-first, rule-based fallback."""
    from .ai_services import generate_with_ai, _try_parse_json, is_ai_available

    if is_ai_available():
        ai_result = _calculate_ats_score_with_ai(extracted_data, target_job_description, raw_text)
        if ai_result:
            return ai_result

    return _calculate_ats_score_with_rules(extracted_data, target_job_description, raw_text)


def _calculate_ats_score_with_ai(extracted_data, target_job_description, raw_text):
    """Use AI to analyze resume and generate ATS scores."""
    from .ai_services import generate_with_ai, _try_parse_json

    skills = ', '.join(extracted_data.get('skills', []))
    experience = extracted_data.get('experience', [])
    education = extracted_data.get('education', [])
    summary = extracted_data.get('summary', '')

    exp_text = ""
    for exp in experience[:5]:
        if isinstance(exp, dict):
            exp_text += f"- {exp.get('title', '')} at {exp.get('company', '')} ({exp.get('duration', '')}): {exp.get('description', '')}\n"
        else:
            exp_text += f"- {exp}\n"

    edu_text = ""
    for edu in education[:3]:
        if isinstance(edu, dict):
            edu_text += f"- {edu.get('text', edu.get('degree', ''))} from {edu.get('institution', '')}\n"
        else:
            edu_text += f"- {edu}\n"

    prompt = f"""You are an expert ATS (Applicant Tracking System) analyzer. Analyze this resume and provide detailed scoring.

Resume Data:
- Name: {extracted_data.get('name', 'N/A')}
- Skills: {skills}
- Summary: {summary}
- Experience: {exp_text if exp_text else 'None listed'}
- Education: {edu_text if edu_text else 'None listed'}
- Has LinkedIn: {'Yes' if extracted_data.get('linkedin_url') else 'No'}
- Has GitHub: {'Yes' if extracted_data.get('github_url') else 'No'}

{f'Target Job Description: {target_job_description[:1000]}' if target_job_description else 'No specific job description provided - score based on general ATS best practices.'}

Evaluate the resume on these dimensions (0-100 each):
1. formatting_score - How well-structured and ATS-friendly is the format
2. skills_match_score - How well skills align with the job/target role
3. experience_score - Quality and relevance of work experience
4. education_score - Educational qualifications
5. keywords_score - Presence of relevant industry keywords
6. projects_score - Quality of demonstrated projects

Also provide:
- suggestions: Array of 5-8 specific, actionable improvement suggestions
- missing_keywords: Array of keywords that would improve the resume

Return as JSON with this EXACT structure:
{{
  "overall_score": number,
  "formatting_score": number,
  "skills_match_score": number,
  "experience_score": number,
  "education_score": number,
  "keywords_score": number,
  "projects_score": number,
  "suggestions": ["suggestion1", "suggestion2", ...],
  "missing_keywords": ["keyword1", "keyword2", ...]
}}

Return ONLY valid JSON, no markdown."""

    response = generate_with_ai(prompt, max_tokens=1500, temperature=0.2)
    parsed = _try_parse_json(response)

    if isinstance(parsed, dict) and 'overall_score' in parsed:
        for key in ['overall_score', 'formatting_score', 'skills_match_score',
                     'experience_score', 'education_score', 'keywords_score', 'projects_score']:
            parsed[key] = min(max(parsed.get(key, 0), 0), 100)
        parsed.setdefault('suggestions', [])
        parsed.setdefault('missing_keywords', [])
        return parsed

    return None


def _calculate_ats_score_with_rules(extracted_data, target_job_description, raw_text):
    """Rule-based ATS scoring (fallback when AI is unavailable)."""
    scores = {}

    formatting_score = _calculate_formatting_score(extracted_data, raw_text)
    skills_score = _calculate_skills_match(extracted_data, target_job_description)
    experience_score = _calculate_experience_score(extracted_data)
    education_score = _calculate_education_score(extracted_data)
    keywords_score = _calculate_keywords_score(raw_text, target_job_description)
    projects_score = _calculate_projects_score(extracted_data)

    scores['formatting_score'] = formatting_score
    scores['skills_match_score'] = skills_score
    scores['experience_score'] = experience_score
    scores['education_score'] = education_score
    scores['keywords_score'] = keywords_score
    scores['projects_score'] = projects_score

    weights = {
        'formatting': 0.15,
        'skills_match': 0.25,
        'experience': 0.20,
        'education': 0.15,
        'keywords': 0.15,
        'projects': 0.10,
    }

    overall = (
        formatting_score * weights['formatting'] +
        skills_score * weights['skills_match'] +
        experience_score * weights['experience'] +
        education_score * weights['education'] +
        keywords_score * weights['keywords'] +
        projects_score * weights['projects']
    )

    scores['overall_score'] = round(min(overall, 100), 1)

    missing = _find_missing_keywords(raw_text, target_job_description)
    suggestions = _generate_suggestions(scores, extracted_data)
    scores['missing_keywords'] = missing
    scores['suggestions'] = suggestions

    return scores


def _calculate_formatting_score(data, raw_text):
    score = 50
    if data.get('name'):
        score += 10
    if data.get('email'):
        score += 10
    if data.get('phone'):
        score += 8
    if data.get('skills'):
        score += 7
    if data.get('education'):
        score += 5
    if data.get('experience'):
        score += 5
    if data.get('summary'):
        score += 5
    if raw_text and len(raw_text) > 500:
        score += 5
    if raw_text and len(raw_text) < 200:
        score -= 10
    if data.get('linkedin_url'):
        score += 3
    if data.get('github_url'):
        score += 2
    return min(score, 100)


def _calculate_skills_match(data, job_description):
    if not job_description:
        if data.get('skills'):
            return min(70 + len(data['skills']) * 2, 100)
        return 30
    job_skills = _extract_skills_from_text(job_description)
    resume_skills = set(s.lower() for s in data.get('skills', []))
    if not job_skills:
        return 50
    matched = resume_skills.intersection(job_skills)
    match_ratio = len(matched) / len(job_skills) if job_skills else 0
    return round(match_ratio * 100, 1)


def _calculate_experience_score(data):
    experience = data.get('experience', [])
    if not experience:
        return 30
    score = 40
    score += min(len(experience) * 15, 40)
    has_details = any(exp.get('description', '') for exp in experience if isinstance(exp, dict))
    if has_details:
        score += 20
    return min(score, 100)


def _calculate_education_score(data):
    education = data.get('education', [])
    if not education:
        return 25
    score = 50
    for edu in education:
        text = edu.get('text', '').lower() if isinstance(edu, dict) else str(edu).lower()
        if any(d in text for d in ['phd', 'doctorate']):
            score = max(score, 100)
        elif any(d in text for d in ['master', 'm.tech', 'm.sc', 'mba', 'mca']):
            score = max(score, 85)
        elif any(d in text for d in ['bachelor', 'b.tech', 'b.sc', 'bca', 'be']):
            score = max(score, 75)
        else:
            score = max(score, 60)
    return min(score, 100)


def _calculate_keywords_score(raw_text, job_description):
    if not raw_text:
        return 30
    text_lower = raw_text.lower()
    important_keywords = ['experience', 'skills', 'developer', 'engineer', 'project',
                          'team', 'developed', 'implemented', 'managed', 'led',
                          'improved', 'achieved', 'delivered', 'optimized']
    found = sum(1 for kw in important_keywords if kw in text_lower)
    score = 30 + (found / len(important_keywords)) * 50
    if job_description:
        job_keywords = re.findall(r'\b\w+\b', job_description.lower())
        common = set(job_keywords).intersection(set(re.findall(r'\b\w+\b', text_lower)))
        keyword_ratio = len(common) / max(len(set(job_keywords)), 1)
        score += keyword_ratio * 20
    return min(round(score, 1), 100)


def _calculate_projects_score(data):
    projects = data.get('projects', [])
    if not projects:
        return 20
    score = 40 + min(len(projects) * 20, 50)
    return min(score, 100)


def _extract_skills_from_text(text):
    skills = set()
    skill_patterns = [
        r'\bpython\b', r'\bjavascript\b', r'\bjava\b', r'\bdjango\b', r'\bflask\b',
        r'\breact\b', r'\bangular\b', r'\bvue\b', r'\bhtml\b', r'\bcss\b',
        r'\bsql\b', r'\bpostgresql\b', r'\bmysql\b', r'\bmongodb\b', r'\bredis\b',
        r'\bdocker\b', r'\bkubernetes\b', r'\baws\b', r'\bazure\b', r'\bgcp\b',
        r'\bgit\b', r'\bci/cd\b', r'\bjenkins\b', r'\bnginx\b',
        r'\brest\s?api\b', r'\bgraphql\b', r'\bjwt\b', r'\boauth\b',
        r'\bcelery\b', r'\brabbitmq\b', r'\bkafka\b',
        r'\bmachine\s?learning\b', r'\bdeep\s?learning\b', r'\bnlp\b',
        r'\btensorflow\b', r'\bpytorch\b', r'\bscikit-learn\b',
        r'\bpandas\b', r'\bnumpy\b', r'\blangchain\b', r'\bopenai\b',
        r'\bpytest\b', r'\bunittest\b', r'\bjest\b',
        r'\blinux\b', r'\bbash\b', r'\bterraform\b',
        r'\bagile\b', r'\bscrum\b', r'\bjira\b',
        r'\bdata\sstructures\b', r'\balgorithms\b', r'\boop\b',
    ]
    text_lower = text.lower()
    for pattern in skill_patterns:
        match = re.search(pattern, text_lower)
        if match:
            skills.add(match.group().strip())
    return skills


def _find_missing_keywords(raw_text, job_description):
    if not job_description:
        return []
    text_lower = raw_text.lower() if raw_text else ""
    job_words = set(re.findall(r'\b\w{3,}\b', job_description.lower()))
    resume_words = set(re.findall(r'\b\w{3,}\b', text_lower))
    common_tech_words = {'python', 'java', 'javascript', 'django', 'flask', 'react', 'aws',
                          'docker', 'kubernetes', 'sql', 'postgresql', 'mongodb', 'redis',
                          'api', 'rest', 'graphql', 'git', 'ci/cd', 'jenkins', 'linux',
                          'nginx', 'celery', 'rabbitmq', 'kafka', 'terraform', 'ansible',
                          'machine', 'learning', 'deep', 'tensorflow', 'pytorch', 'nlp',
                          'pandas', 'numpy', 'scikit', 'pytest', 'agile', 'scrum'}
    missing = job_words.intersection(common_tech_words) - resume_words
    return list(missing)[:20]


def _generate_suggestions(scores, data):
    suggestions = []
    if scores['formatting_score'] < 70:
        if not data.get('name'):
            suggestions.append("Add your full name at the top of the resume.")
        if not data.get('email'):
            suggestions.append("Add your professional email address.")
        if not data.get('phone'):
            suggestions.append("Add your phone number for contact.")
        if not data.get('summary'):
            suggestions.append("Add a professional summary/objective section.")
    if scores['skills_match_score'] < 60:
        suggestions.append("Add more relevant skills that match the target job description.")
        suggestions.append("Include both technical and soft skills in your skills section.")
    if scores['experience_score'] < 60:
        if not data.get('experience'):
            suggestions.append("Add work experience with specific achievements and metrics.")
        else:
            suggestions.append("Enhance your experience descriptions with quantifiable achievements.")
            suggestions.append("Use action verbs like 'Developed', 'Implemented', 'Led', 'Optimized'.")
    if scores['education_score'] < 50:
        suggestions.append("Add your educational qualifications with institution names and years.")
    if scores['projects_score'] < 50:
        suggestions.append("Add personal or professional projects to demonstrate your skills.")
    if scores['keywords_score'] < 50:
        suggestions.append("Include more industry-relevant keywords in your resume.")
    if not data.get('linkedin_url'):
        suggestions.append("Add your LinkedIn profile URL.")
    return suggestions[:10]
