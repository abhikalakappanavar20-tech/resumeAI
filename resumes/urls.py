from django.urls import path
from . import views

app_name = 'resumes'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('upload/', views.upload_resume, name='upload'),
    path('<uuid:pk>/', views.resume_detail, name='resume_detail'),
    path('<uuid:pk>/delete/', views.delete_resume, name='delete'),
    path('history/', views.resume_history, name='history'),
]
