import os
import re
import json

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

try:
    from docx import Document
except ImportError:
    Document = None


def extract_text_from_pdf(file_path):
    """Extract text from PDF using pypdf."""
    text = ""
    if PdfReader:
        try:
            reader = PdfReader(file_path)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            if text.strip():
                return text
        except Exception:
            pass
    return text


def extract_text_from_docx(file_path):
    """Extract text from DOCX file."""
    if not Document:
        return "Error: python-docx not installed"
    try:
        doc = Document(file_path)
        text = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
        return text
    except Exception as e:
        return f"Error extracting DOCX: {str(e)}"


def extract_text(file_path):
    """Extract text from file based on extension."""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.pdf':
        return extract_text_from_pdf(file_path)
    elif ext in ['.docx', '.doc']:
        return extract_text_from_docx(file_path)
    return ""


def extract_email(text):
    """Extract email from text."""
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = re.findall(pattern, text)
    return emails[0] if emails else ""


def extract_phone(text):
    """Extract phone numbers from text."""
    patterns = [
        r'[\+]?[\d]{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
        r'\d{10}',
        r'\d{3}[-.\s]\d{3}[-.\s]\d{4}',
    ]
    for pattern in patterns:
        phones = re.findall(pattern, text)
        if phones:
            return phones[0].strip()
    return ""


def extract_links(text):
    """Extract LinkedIn, GitHub, and portfolio URLs."""
    urls = re.findall(r'https?://[^\s]+', text)
    linkedin = ""
    github = ""
    portfolio = ""
    for url in urls:
        if 'linkedin.com' in url:
            linkedin = url
        elif 'github.com' in url:
            github = url
        elif any(d in url for d in ['.dev', '.io', '.com', 'portfolio']):
            if not portfolio:
                portfolio = url
    return linkedin, github, portfolio


def extract_name(text):
    """Extract name from resume text (usually the first non-empty line)."""
    lines = text.strip().split('\n')
    for line in lines:
        line = line.strip()
        if line and len(line) > 2 and len(line) < 100:
            if not any(char.isdigit() for char in line):
                if not any(w in line.lower() for w in ['resume', 'cv', 'contact', 'email', 'phone', 'address', 'objective', 'summary']):
                    words = line.split()
                    if 1 <= len(words) <= 5:
                        return line
    return ""


def extract_section(text, section_keywords):
    """Extract a section from resume text by keyword headers."""
    lines = text.split('\n')
    section_lines = []
    in_section = False
    for line in lines:
        line_lower = line.lower().strip()
        if any(kw in line_lower for kw in section_keywords):
            in_section = True
            continue
        if in_section:
            if line.strip() == '' or (len(line.strip()) > 0 and line.strip()[-1] == ':' and len(section_lines) > 0):
                if len(section_lines) > 0 and line.strip() == '':
                    continue
                if len(section_lines) > 0:
                    break
            section_lines.append(line.strip())
    return '\n'.join(filter(None, section_lines))


SKILLS_DATABASE = [
    "python", "javascript", "java", "c++", "c#", "ruby", "go", "rust", "php", "swift",
    "kotlin", "typescript", "scala", "r", "matlab", "perl",
    "django", "flask", "fastapi", "express", "spring", "rails", "laravel", "asp.net",
    "react", "angular", "vue", "svelte", "next.js", "nuxt.js", "bootstrap", "tailwind",
    "html", "css", "sass", "less",
    "postgresql", "mysql", "mongodb", "redis", "elasticsearch", "sqlite", "oracle", "cassandra",
    "dynamodb", "firebase",
    "aws", "azure", "gcp", "docker", "kubernetes", "jenkins", "ci/cd", "terraform", "ansible",
    "nginx", "apache",
    "git", "github", "gitlab", "bitbucket", "jira", "confluence",
    "machine learning", "deep learning", "nlp", "natural language processing",
    "tensorflow", "pytorch", "keras", "scikit-learn", "pandas", "numpy", "matplotlib",
    "opencv", "transformers",
    "rest api", "restful api", "graphql", "grpc", "websocket",
    "agile", "scrum", "jira", "trello",
    "linux", "unix", "bash", "powershell",
    "jwt", "oauth", "saml",
    "celery", "rabbitmq", "kafka",
    "pytest", "unittest", "jest", "selenium", "cypress",
    "orm", "sqlalchemy", "django orm",
    "data structures", "algorithms", "oop", "solid principles",
    "communication", "leadership", "teamwork", "problem solving",
]


def extract_skills_regex(text):
    """Extract skills from resume text using pattern matching."""
    text_lower = text.lower()
    found_skills = []
    for skill in SKILLS_DATABASE:
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, text_lower):
            found_skills.append(skill)
    return list(set(found_skills))


def parse_with_regex(text):
    """Parse resume using regex-based extraction (fallback method)."""
    linkedin, github, portfolio = extract_links(text)

    return {
        'name': extract_name(text),
        'email': extract_email(text),
        'phone': extract_phone(text),
        'location': '',
        'linkedin_url': linkedin,
        'github_url': github,
        'portfolio_url': portfolio,
        'skills': extract_skills_regex(text),
        'education': extract_education_regex(text),
        'experience': extract_experience_regex(text),
        'projects': extract_projects_regex(text),
        'certifications': extract_certifications_regex(text),
        'summary': extract_section(text, ['summary', 'objective', 'profile', 'about']),
        'languages': [],
        'interests': [],
    }


def extract_education_regex(text):
    """Extract education information using regex."""
    education = []
    degree_patterns = re.findall(
        r'(Bachelor|Master|PhD|B\.?Tech|M\.?Tech|B\.?Sc|M\.?Sc|B\.?CA|M\.?CA|BE|ME|MBA)[^\n]*',
        text, re.IGNORECASE
    )
    for d in degree_patterns:
        education.append({'text': d.strip(), 'degree': d, 'institution': '', 'year': ''})

    if not education:
        edu_section = extract_section(text, ['education', 'academic', 'qualification', 'degree'])
        if edu_section:
            for line in edu_section.split('\n'):
                if line.strip():
                    education.append({'text': line.strip(), 'degree': '', 'institution': '', 'year': ''})
    return education


def extract_experience_regex(text):
    """Extract work experience information using regex."""
    experience = []
    exp_section = extract_section(text, ['experience', 'work history', 'employment', 'professional experience'])
    if exp_section:
        lines = exp_section.split('\n')
        current_exp = {}
        for line in lines:
            if re.search(r'\d{4}\s*[-–]\s*(?:\d{4}|present|current)', line, re.IGNORECASE):
                if current_exp:
                    experience.append(current_exp)
                current_exp = {'duration': line.strip(), 'description': ''}
            elif current_exp:
                current_exp['description'] += line.strip() + ' '
        if current_exp:
            experience.append(current_exp)
    return experience


def extract_projects_regex(text):
    """Extract project information using regex."""
    projects = []
    proj_section = extract_section(text, ['projects', 'project experience', 'personal projects'])
    if proj_section:
        for line in proj_section.split('\n'):
            if line.strip() and len(line.strip()) > 5:
                projects.append({'name': line.strip(), 'description': ''})
    return projects


def extract_certifications_regex(text):
    """Extract certifications using regex."""
    certifications = []
    cert_section = extract_section(text, ['certifications', 'certificates', 'licenses'])
    if cert_section:
        for line in cert_section.split('\n'):
            if line.strip():
                certifications.append(line.strip())
    return certifications


def parse_resume_with_ai(file_path):
    """Parse resume using AI extraction. Returns (extracted_data, raw_text)."""
    text = extract_text(file_path)
    if not text or text.startswith("Error"):
        return None, text

    from .ai_services import generate_with_ai, _try_parse_json

    prompt = f"""You are an expert resume parser AI. Extract ALL information from this resume text and return it as structured JSON.

Resume Text:
{text[:4000]}

Extract the following fields and return ONLY valid JSON:
{{
  "name": "full name of the candidate",
  "email": "email address",
  "phone": "phone number",
  "location": "city, state/country",
  "linkedin_url": "linkedin profile URL or empty string",
  "github_url": "github profile URL or empty string",
  "portfolio_url": "portfolio URL or empty string",
  "summary": "professional summary/objective or empty string",
  "skills": ["skill1", "skill2", ...],
  "education": [
    {{"text": "full education line", "degree": "degree type", "institution": "school name", "year": "graduation year"}}
  ],
  "experience": [
    {{"title": "job title", "company": "company name", "duration": "start - end", "description": "what they did"}}
  ],
  "projects": [
    {{"name": "project name", "description": "what it does", "technologies": ["tech1", "tech2"]}}
  ],
  "certifications": ["cert1", "cert2", ...],
  "languages": ["language1", "language2", ...],
  "interests": ["interest1", "interest2", ...]
}}

Rules:
- Extract EXACTLY what appears in the resume, do not fabricate information
- For skills, extract ALL technical and soft skills mentioned anywhere in the resume
- For experience, extract each job/position with title, company, duration, and description
- For education, extract degrees, institutions, and years
- Return ONLY the JSON object, no markdown, no extra text"""

    response = generate_with_ai(prompt, max_tokens=2500, temperature=0.1)
    parsed = _try_parse_json(response)

    if isinstance(parsed, dict):
        parsed = _ensure_all_fields(parsed)
        return parsed, text

    regex_result = parse_with_regex(text)
    return regex_result, text


def _ensure_all_fields(data):
    """Ensure all expected fields exist with proper defaults."""
    defaults = {
        'name': '',
        'email': '',
        'phone': '',
        'location': '',
        'linkedin_url': '',
        'github_url': '',
        'portfolio_url': '',
        'summary': '',
        'skills': [],
        'education': [],
        'experience': [],
        'projects': [],
        'certifications': [],
        'languages': [],
        'interests': [],
    }
    for key, default in defaults.items():
        if key not in data:
            data[key] = default
    return data


def parse_resume(file_path):
    """Main function to parse resume. AI-first, regex fallback."""
    from .ai_services import is_ai_available

    text = extract_text(file_path)
    if not text or text.startswith("Error"):
        return None, text

    if is_ai_available():
        extracted, _ = parse_resume_with_ai(file_path)
        if extracted:
            return extracted, text

    regex_result = parse_with_regex(text)
    return regex_result, text
