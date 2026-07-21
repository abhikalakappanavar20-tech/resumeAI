from rest_framework import serializers
from resumes.models import (Resume, ExtractedResumeData, ATSScore, CoverLetter,
                            InterviewQuestion, SkillGap, Skill, ResumeImprovement)


class ResumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resume
        fields = ['id', 'title', 'file', 'file_type', 'file_size', 'status', 'created_at', 'updated_at']
        read_only_fields = ['id', 'file_type', 'file_size', 'status', 'created_at', 'updated_at']


class ExtractedResumeDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExtractedResumeData
        fields = '__all__'


class ATSScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = ATSScore
        fields = '__all__'


class CoverLetterSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoverLetter
        fields = '__all__'


class InterviewQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewQuestion
        fields = '__all__'


class SkillGapSerializer(serializers.ModelSerializer):
    class Meta:
        model = SkillGap
        fields = '__all__'


class ResumeImprovementSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResumeImprovement
        fields = '__all__'


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = '__all__'
