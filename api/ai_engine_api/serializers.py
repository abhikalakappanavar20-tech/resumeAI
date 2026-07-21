from rest_framework import serializers


class CoverLetterRequestSerializer(serializers.Serializer):
    company = serializers.CharField(max_length=200)
    role = serializers.CharField(max_length=200)
    job_description = serializers.CharField(required=False, allow_blank=True)
    tone = serializers.CharField(default='professional')


class SkillGapRequestSerializer(serializers.Serializer):
    target_role = serializers.CharField(max_length=200)


class InterviewQuestionsRequestSerializer(serializers.Serializer):
    skills = serializers.ListField(child=serializers.CharField(), required=False)
