from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='api-register'),
    path('login/', TokenObtainPairView.as_view(), name='api-token-obtain'),
    path('token/refresh/', TokenRefreshView.as_view(), name='api-token-refresh'),
    path('profile/', views.ProfileView.as_view(), name='api-profile'),
    path('candidates/', views.CandidateListView.as_view(), name='api-candidates'),
]
