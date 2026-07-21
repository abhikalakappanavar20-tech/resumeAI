from django.contrib import admin
from .models import (Resume, ExtractedResumeData, Skill, ATSScore,
                     CoverLetter, InterviewQuestion, SkillGap, ResumeImprovement)

@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'file_type', 'status', 'created_at']
    list_filter = ['status', 'file_type']
    search_fields = ['title', 'user__username']

@admin.register(ExtractedResumeData)
class ExtractedResumeDataAdmin(admin.ModelAdmin):
    list_display = ['resume', 'name', 'email']

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'popularity_score']
    list_filter = ['category']
    search_fields = ['name']

@admin.register(ATSScore)
class ATSScoreAdmin(admin.ModelAdmin):
    list_display = ['resume', 'overall_score', 'formatting_score', 'skills_match_score']

@admin.register(CoverLetter)
class CoverLetterAdmin(admin.ModelAdmin):
    list_display = ['resume', 'company_name', 'job_title', 'created_at']

@admin.register(InterviewQuestion)
class InterviewQuestionAdmin(admin.ModelAdmin):
    list_display = ['resume', 'skill', 'question', 'difficulty']

@admin.register(SkillGap)
class SkillGapAdmin(admin.ModelAdmin):
    list_display = ['resume', 'target_role', 'match_percentage']

@admin.register(ResumeImprovement)
class ResumeImprovementAdmin(admin.ModelAdmin):
    list_display = ['resume', 'section']
