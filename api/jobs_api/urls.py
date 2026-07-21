from django.urls import path
from . import views

urlpatterns = [
    path('', views.JobListCreateView.as_view(), name='api-job-list'),
    path('<uuid:pk>/', views.JobDetailView.as_view(), name='api-job-detail'),
    path('<uuid:pk>/apply/', views.ApplyJobView.as_view(), name='api-apply-job'),
    path('my-applications/', views.MyApplicationsView.as_view(), name='api-my-applications'),
    path('recommendations/', views.JobRecommendationsView.as_view(), name='api-job-recommendations'),
]
