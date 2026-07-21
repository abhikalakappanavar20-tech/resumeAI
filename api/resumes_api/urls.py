from django.urls import path
from . import views

urlpatterns = [
    path('', views.ResumeListCreateView.as_view(), name='api-resume-list'),
    path('<uuid:pk>/', views.ResumeDetailView.as_view(), name='api-resume-detail'),
    path('<uuid:pk>/analysis/', views.ResumeAnalysisView.as_view(), name='api-resume-analysis'),
    path('skills/', views.SkillListView.as_view(), name='api-skill-list'),
]
