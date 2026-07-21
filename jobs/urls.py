from django.urls import path
from . import views

app_name = 'jobs'

urlpatterns = [
    path('', views.job_list, name='job_list'),
    path('create/', views.create_job, name='create'),
    path('my-jobs/', views.my_jobs, name='my_jobs'),
    path('my-applications/', views.my_applications, name='my_applications'),
    path('<uuid:pk>/', views.job_detail, name='job_detail'),
    path('<uuid:pk>/edit/', views.edit_job, name='edit'),
    path('<uuid:pk>/delete/', views.delete_job, name='delete'),
    path('<uuid:pk>/apply/', views.apply_job, name='apply'),
    path('<uuid:pk>/applications/', views.job_applications, name='job_applications'),
]
