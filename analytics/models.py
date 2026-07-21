from django.db import models
from django.conf import settings


class AIUsageLog(models.Model):
    AI_FEATURE_CHOICES = (
        ('resume_parsing', 'Resume Parsing'),
        ('ats_scoring', 'ATS Scoring'),
        ('cover_letter', 'Cover Letter Generation'),
        ('interview_questions', 'Interview Question Generation'),
        ('job_matching', 'Job Matching'),
        ('skill_gap', 'Skill Gap Analysis'),
        ('resume_improvement', 'Resume Improvement'),
        ('candidate_ranking', 'Candidate Ranking'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ai_usage_logs')
    feature = models.CharField(max_length=30, choices=AI_FEATURE_CHOICES)
    tokens_used = models.IntegerField(default=0)
    response_time_ms = models.IntegerField(default=0)
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.feature}"


class PlatformAnalytics(models.Model):
    date = models.DateField(unique=True)
    total_users = models.IntegerField(default=0)
    new_registrations = models.IntegerField(default=0)
    active_candidates = models.IntegerField(default=0)
    active_recruiters = models.IntegerField(default=0)
    total_resumes = models.IntegerField(default=0)
    total_jobs = models.IntegerField(default=0)
    total_applications = models.IntegerField(default=0)
    total_ai_requests = models.IntegerField(default=0)
    avg_ats_score = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Platform Analytics'
        ordering = ['-date']

    def __str__(self):
        return f"Analytics: {self.date}"
