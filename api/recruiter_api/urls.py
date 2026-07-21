from django.urls import path
from . import views

urlpatterns = [
    path('shortlist/', views.ShortlistView.as_view(), name='api-shortlist'),
    path('search/', views.SearchCandidatesView.as_view(), name='api-search-candidates'),
]
