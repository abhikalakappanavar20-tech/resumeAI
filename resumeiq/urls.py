from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('api/', include('api.urls')),
    path('accounts/', include('accounts.urls')),
    path('resumes/', include('resumes.urls')),
    path('jobs/', include('jobs.urls')),
    path('recruiter/', include('recruiter.urls')),
    path('analytics/', include('analytics.urls')),
    path('ai_engine/', include('ai_engine.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
