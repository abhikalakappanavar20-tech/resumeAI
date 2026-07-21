from django.urls import path
from . import views

app_name = 'recruiter'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('search/', views.search_candidates, name='search_candidates'),
    path('shortlist/', views.my_shortlist, name='shortlist'),
    path('candidate/<int:pk>/', views.candidate_profile, name='candidate_profile'),
    path('candidate/<int:pk>/shortlist/', views.shortlist_candidate, name='shortlist_candidate'),
    path('job/<uuid:job_pk>/rank/', views.rank_candidates, name='rank_candidates'),
]
