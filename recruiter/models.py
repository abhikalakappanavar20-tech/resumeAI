from django.db import models
from django.conf import settings


class CandidateShortlist(models.Model):
    recruiter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='shortlisted_candidates')
    candidate = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='shortlisted_by')
    job = models.ForeignKey('jobs.Job', on_delete=models.CASCADE, null=True, blank=True)
    notes = models.TextField(blank=True)
    ai_score = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['recruiter', 'candidate', 'job']

    def __str__(self):
        return f"{self.recruiter.username} shortlisted {self.candidate.username}"


class CandidateSearch(models.Model):
    recruiter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    query = models.CharField(max_length=200)
    filters_used = models.JSONField(default=dict)
    results_count = models.IntegerField(default=0)
    searched_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Search: {self.query}"
