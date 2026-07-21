from django.db import models
from django.conf import settings
import uuid


class Resume(models.Model):
    STATUS_CHOICES = (
        ('uploaded', 'Uploaded'),
        ('parsing', 'Parsing'),
        ('parsed', 'Parsed'),
        ('analyzed', 'Analyzed'),
        ('error', 'Error'),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='resumes')
    title = models.CharField(max_length=200, default='Untitled Resume')
    file = models.FileField(upload_to='resumes/')
    file_type = models.CharField(max_length=10, blank=True)
    file_size = models.BigIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='uploaded')
    raw_text = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.user.username}"


class ExtractedResumeData(models.Model):
    resume = models.OneToOneField(Resume, on_delete=models.CASCADE, related_name='extracted_data')
    name = models.CharField(max_length=200, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    location = models.CharField(max_length=200, blank=True)
    linkedin_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)
    portfolio_url = models.URLField(blank=True)
    summary = models.TextField(blank=True)
    skills = models.JSONField(default=list, blank=True)
    education = models.JSONField(default=list, blank=True)
    experience = models.JSONField(default=list, blank=True)
    projects = models.JSONField(default=list, blank=True)
    certifications = models.JSONField(default=list, blank=True)
    languages = models.JSONField(default=list, blank=True)
    interests = models.JSONField(default=list, blank=True)
    raw_sections = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Extracted Data: {self.resume.title}"


class Skill(models.Model):
    CATEGORY_CHOICES = (
        ('programming', 'Programming Language'),
        ('framework', 'Framework'),
        ('database', 'Database'),
        ('tool', 'Tool'),
        ('cloud', 'Cloud Platform'),
        ('soft', 'Soft Skill'),
        ('other', 'Other'),
    )
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    normalized_name = models.CharField(max_length=100, unique=True)
    popularity_score = models.FloatField(default=0)

    class Meta:
        ordering = ['-popularity_score']

    def __str__(self):
        return self.name


class ATSScore(models.Model):
    resume = models.OneToOneField(Resume, on_delete=models.CASCADE, related_name='ats_score')
    overall_score = models.FloatField(default=0)
    formatting_score = models.FloatField(default=0)
    skills_match_score = models.FloatField(default=0)
    experience_score = models.FloatField(default=0)
    education_score = models.FloatField(default=0)
    keywords_score = models.FloatField(default=0)
    projects_score = models.FloatField(default=0)
    suggestions = models.JSONField(default=list, blank=True)
    missing_keywords = models.JSONField(default=list, blank=True)
    target_job_description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"ATS Score: {self.overall_score} - {self.resume.title}"


class CoverLetter(models.Model):
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='cover_letters')
    company_name = models.CharField(max_length=200)
    job_title = models.CharField(max_length=200)
    content = models.TextField()
    tone = models.CharField(max_length=50, default='professional')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cover Letter: {self.job_title} at {self.company_name}"


class InterviewQuestion(models.Model):
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='interview_questions')
    skill = models.CharField(max_length=100)
    question = models.TextField()
    expected_answer = models.TextField(blank=True)
    difficulty = models.CharField(max_length=20, default='medium')
    category = models.CharField(max_length=50, default='technical')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Q: {self.question[:50]}"


class SkillGap(models.Model):
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='skill_gaps')
    target_role = models.CharField(max_length=200)
    current_skills = models.JSONField(default=list)
    missing_skills = models.JSONField(default=list)
    recommendations = models.JSONField(default=list)
    learning_roadmap = models.JSONField(default=list)
    match_percentage = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Skill Gap: {self.target_role}"


class ResumeImprovement(models.Model):
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='improvements')
    section = models.CharField(max_length=100)
    original_text = models.TextField()
    improved_text = models.TextField()
    explanation = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Improvement: {self.section}"
