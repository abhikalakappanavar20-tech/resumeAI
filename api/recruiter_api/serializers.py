from rest_framework import serializers
from recruiter.models import CandidateShortlist, CandidateSearch


class CandidateShortlistSerializer(serializers.ModelSerializer):
    class Meta:
        model = CandidateShortlist
        fields = '__all__'
        read_only_fields = ['recruiter']
