from django.contrib import admin
from .models import Job, Application, JobRecommendation

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ['title', 'company_name', 'recruiter', 'job_type', 'status', 'applicants_count', 'created_at']
    list_filter = ['status', 'job_type', 'experience_required']
    search_fields = ['title', 'company_name', 'description']

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ['candidate', 'job', 'status', 'ai_match_score', 'applied_at']
    list_filter = ['status']

@admin.register(JobRecommendation)
class JobRecommendationAdmin(admin.ModelAdmin):
    list_display = ['candidate', 'job', 'match_score']
