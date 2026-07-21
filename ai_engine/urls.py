from django.urls import path
from . import views

app_name = 'ai_engine'

urlpatterns = [
    path('analyze/<uuid:pk>/', views.analyze_resume, name='analyze'),
    path('<uuid:pk>/cover-letter/', views.generate_cover_letter_view, name='cover_letter'),
    path('<uuid:pk>/interview-questions/', views.generate_interview_questions_view, name='interview_questions'),
    path('<uuid:pk>/improvements/', views.generate_improvements_view, name='improvements'),
    path('<uuid:pk>/skill-gap/', views.skill_gap_analysis_view, name='skill_gap'),
    path('<uuid:pk>/job-recommendations/', views.job_recommendations_view, name='job_recommendations'),
    path('api/analyze/<uuid:pk>/', views.analyze_resume_api, name='analyze_api'),
]
