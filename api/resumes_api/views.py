from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from resumes.models import (Resume, ExtractedResumeData, ATSScore, Skill)
from .serializers import ResumeSerializer, ExtractedResumeDataSerializer, ATSScoreSerializer, SkillSerializer


class ResumeListCreateView(generics.ListCreateAPIView):
    serializer_class = ResumeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Resume.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        resume = serializer.save(user=self.request.user)
        resume.file_type = resume.file.name.split('.')[-1].lower()
        resume.file_size = resume.file.size
        resume.save()


class ResumeDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = ResumeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Resume.objects.filter(user=self.request.user)


class ResumeAnalysisView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            resume = Resume.objects.get(pk=pk, user=request.user)
        except Resume.DoesNotExist:
            return Response({"error": "Resume not found"}, status=status.HTTP_404_NOT_FOUND)
        
        data = {"resume": ResumeSerializer(resume).data}
        try:
            data["extracted_data"] = ExtractedResumeDataSerializer(resume.extracted_data).data
        except ExtractedResumeData.DoesNotExist:
            data["extracted_data"] = None
        
        try:
            data["ats_score"] = ATSScoreSerializer(resume.ats_score).data
        except ATSScore.DoesNotExist:
            data["ats_score"] = None
        
        return Response(data)


class SkillListView(generics.ListAPIView):
    serializer_class = SkillSerializer
    permission_classes = [permissions.AllowAny]
    queryset = Skill.objects.all()
