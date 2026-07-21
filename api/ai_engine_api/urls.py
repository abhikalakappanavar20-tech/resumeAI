from django.urls import path
from . import views

urlpatterns = [
    path('analyze/<uuid:pk>/', views.AnalyzeResumeView.as_view(), name='api-analyze-resume'),
    path('<uuid:pk>/cover-letter/', views.GenerateCoverLetterView.as_view(), name='api-generate-cover-letter'),
    path('<uuid:pk>/interview-questions/', views.GenerateInterviewQuestionsView.as_view(), name='api-generate-questions'),
    path('<uuid:pk>/skill-gap/', views.SkillGapAnalysisView.as_view(), name='api-skill-gap'),
    path('<uuid:pk>/job-recommendations/', views.JobRecommendationsView.as_view(), name='api-job-recommendations'),
    path('<uuid:pk>/improvements/', views.GenerateImprovementsView.as_view(), name='api-generate-improvements'),
]
