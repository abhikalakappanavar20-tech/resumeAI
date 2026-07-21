from django.contrib import admin
from .models import CandidateShortlist, CandidateSearch

@admin.register(CandidateShortlist)
class CandidateShortlistAdmin(admin.ModelAdmin):
    list_display = ['recruiter', 'candidate', 'job', 'ai_score', 'created_at']

@admin.register(CandidateSearch)
class CandidateSearchAdmin(admin.ModelAdmin):
    list_display = ['recruiter', 'query', 'results_count', 'searched_at']
