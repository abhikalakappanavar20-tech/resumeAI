from django.urls import path, include

app_name = 'api'

urlpatterns = [
    path('accounts/', include('api.accounts_api.urls')),
    path('resumes/', include('api.resumes_api.urls')),
    path('jobs/', include('api.jobs_api.urls')),
    path('ai-engine/', include('api.ai_engine_api.urls')),
    path('recruiter/', include('api.recruiter_api.urls')),
    path('analytics/', include('api.analytics_api.urls')),
]
