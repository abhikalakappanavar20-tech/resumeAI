from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Count, Avg, Sum
from accounts.models import User
from resumes.models import Resume
from jobs.models import Job, Application
from analytics.models import AIUsageLog


class AdminStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if not request.user.is_superuser and request.user.role != 'admin':
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)
        
        data = {
            "total_users": User.objects.count(),
            "total_candidates": User.objects.filter(role='candidate').count(),
            "total_recruiters": User.objects.filter(role='recruiter').count(),
            "total_resumes": Resume.objects.count(),
            "total_jobs": Job.objects.count(),
            "total_applications": Application.objects.count(),
            "total_ai_requests": AIUsageLog.objects.count(),
            "avg_ats_score": Resume.objects.filter(
                ats_score__isnull=False
            ).aggregate(avg=Avg('ats_score__overall_score'))['avg'] or 0,
        }
        return Response(data)
