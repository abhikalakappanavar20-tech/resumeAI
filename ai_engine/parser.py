import os
import re

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    from docx import Document
except ImportError:
    Document = None


def extract_text_from_pdf(file_path):
    """Extract text from PDF using pypdf with fallback to pdfplumber."""
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
    if pdfplumber:
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            return f"Error extracting PDF: {str(e)}"
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


def extract_skills(text):
    """Extract skills from resume text using pattern matching."""
    text_lower = text.lower()
    found_skills = []
    for skill in SKILLS_DATABASE:
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, text_lower):
            found_skills.append(skill)
    return list(set(found_skills))


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


def extract_education(text):
    """Extract education information."""
    education_section = extract_section(text, ['education', 'academic', 'qualification', 'degree'])
    education = []
    if education_section:
        lines = education_section.split('\n')
        for line in lines:
            if any(kw in line.lower() for kw in ['bachelor', 'master', 'phd', 'b.tech', 'm.tech', 'b.sc', 'm.sc',
                                                    'mba', 'bca', 'mca', 'be', 'me', 'diploma', 'university', 'college',
                                                    'institute', 'school']):
                education.append({'text': line.strip(), 'degree': '', 'institution': '', 'year': ''})
    if not education:
        degree_patterns = re.findall(r'(Bachelor|Master|PhD|B\.?Tech|M\.?Tech|B\.?Sc|M\.?Sc|B\.?CA|M\.?CA|BE|ME|MBA)[^\n]*', text, re.IGNORECASE)
        for d in degree_patterns:
            education.append({'text': d.strip(), 'degree': d, 'institution': '', 'year': ''})
    return education


def extract_experience(text):
    """Extract work experience information."""
    exp_section = extract_section(text, ['experience', 'work history', 'employment', 'professional experience'])
    experience = []
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


def extract_projects(text):
    """Extract project information."""
    proj_section = extract_section(text, ['projects', 'project experience', 'personal projects'])
    projects = []
    if proj_section:
        lines = proj_section.split('\n')
        for line in lines:
            if line.strip() and len(line.strip()) > 5:
                projects.append({'name': line.strip(), 'description': ''})
    return projects


def extract_certifications(text):
    """Extract certifications."""
    cert_section = extract_section(text, ['certifications', 'certificates', 'licenses'])
    certifications = []
    if cert_section:
        lines = cert_section.split('\n')
        for line in lines:
            if line.strip():
                certifications.append(line.strip())
    return certifications


def parse_resume(file_path):
    """Main function to parse resume and extract all information."""
    text = extract_text(file_path)
    if not text or text.startswith("Error"):
        return None, text

    linkedin, github, portfolio = extract_links(text)

    extracted = {
        'name': extract_name(text),
        'email': extract_email(text),
        'phone': extract_phone(text),
        'linkedin_url': linkedin,
        'github_url': github,
        'portfolio_url': portfolio,
        'skills': extract_skills(text),
        'education': extract_education(text),
        'experience': extract_experience(text),
        'projects': extract_projects(text),
        'certifications': extract_certifications(text),
        'summary': extract_section(text, ['summary', 'objective', 'profile', 'about']),
    }
    return extracted, text
