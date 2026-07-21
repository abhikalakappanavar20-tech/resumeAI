from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('dashboard/', views.admin_dashboard, name='dashboard'),
    path('users/', views.manage_users, name='manage_users'),
    path('jobs/', views.manage_jobs, name='manage_jobs'),
    path('ai-usage/', views.ai_usage_report, name='ai_usage'),
]
