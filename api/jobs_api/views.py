from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from jobs.models import Job, Application, JobRecommendation
from .serializers import JobSerializer, JobListSerializer, ApplicationSerializer, JobRecommendationSerializer


class JobListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return JobSerializer
        return JobListSerializer

    def get_queryset(self):
        queryset = Job.objects.filter(status='active')
        search = self.request.query_params.get('search', '')
        if search:
            from django.db.models import Q
            queryset = queryset.filter(Q(title__icontains=search) | Q(company_name__icontains=search))
        return queryset

    def perform_create(self, serializer):
        serializer.save(recruiter=self.request.user)


class JobDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = JobSerializer
    queryset = Job.objects.all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class ApplyJobView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            job = Job.objects.get(pk=pk)
        except Job.DoesNotExist:
            return Response({"error": "Job not found"}, status=status.HTTP_404_NOT_FOUND)
        
        if Application.objects.filter(job=job, candidate=request.user).exists():
            return Response({"error": "Already applied"}, status=status.HTTP_400_BAD_REQUEST)
        
        application = Application.objects.create(
            job=job,
            candidate=request.user,
            cover_letter=request.data.get('cover_letter', ''),
            resume_id=request.data.get('resume_id')
        )
        job.applicants_count += 1
        job.save(update_fields=['applicants_count'])
        return Response(ApplicationSerializer(application).data, status=status.HTTP_201_CREATED)


class MyApplicationsView(generics.ListAPIView):
    serializer_class = ApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Application.objects.filter(candidate=self.request.user)


class JobRecommendationsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        recommendations = JobRecommendation.objects.filter(candidate=request.user)[:10]
        serializer = JobRecommendationSerializer(recommendations, many=True)
        return Response(serializer.data)
