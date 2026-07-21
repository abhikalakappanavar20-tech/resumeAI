from django.contrib import admin
from .models import AIUsageLog, PlatformAnalytics

@admin.register(AIUsageLog)
class AIUsageLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'feature', 'tokens_used', 'response_time_ms', 'success', 'created_at']
    list_filter = ['feature', 'success']

@admin.register(PlatformAnalytics)
class PlatformAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['date', 'total_users', 'total_resumes', 'total_jobs', 'total_applications', 'total_ai_requests']
