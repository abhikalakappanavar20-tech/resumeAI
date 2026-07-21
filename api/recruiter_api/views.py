from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from recruiter.models import CandidateShortlist
from accounts.models import CandidateProfile
from .serializers import CandidateShortlistSerializer


class ShortlistView(generics.ListCreateAPIView):
    serializer_class = CandidateShortlistSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CandidateShortlist.objects.filter(recruiter=self.request.user)

    def perform_create(self, serializer):
        serializer.save(recruiter=self.request.user)


class SearchCandidatesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        skill = request.query_params.get('skill', '')
        location = request.query_params.get('location', '')
        experience = request.query_params.get('experience', '')
        
        queryset = CandidateProfile.objects.all()
        if skill:
            queryset = queryset.filter(skills__contains=[skill])
        if location:
            queryset = queryset.filter(location__icontains=location)
        if experience:
            queryset = queryset.filter(total_experience_years__gte=int(experience))
        
        from accounts.serializers import CandidateProfileSerializer
        serializer = CandidateProfileSerializer(queryset[:20], many=True)
        return Response(serializer.data)
