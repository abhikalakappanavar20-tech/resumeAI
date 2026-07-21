from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from accounts.models import User, CandidateProfile, RecruiterProfile
from .serializers import UserSerializer, RegisterSerializer, CandidateProfileSerializer, RecruiterProfileSerializer


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        serializer = UserSerializer(user)
        data = serializer.data
        if user.role == 'candidate':
            try:
                profile = CandidateProfile.objects.get(user=user)
                data['profile'] = CandidateProfileSerializer(profile).data
            except CandidateProfile.DoesNotExist:
                data['profile'] = None
        elif user.role == 'recruiter':
            try:
                profile = RecruiterProfile.objects.get(user=user)
                data['profile'] = RecruiterProfileSerializer(profile).data
            except RecruiterProfile.DoesNotExist:
                data['profile'] = None
        return Response(data)

    def put(self, request):
        user = request.user
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CandidateListView(generics.ListAPIView):
    serializer_class = CandidateProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = CandidateProfile.objects.all()
        skill = self.request.query_params.get('skill')
        if skill:
            queryset = queryset.filter(skills__contains=[skill])
        return queryset
