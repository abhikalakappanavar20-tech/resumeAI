from rest_framework import serializers
from jobs.models import Job, Application, JobRecommendation


class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = '__all__'
        read_only_fields = ['recruiter', 'applicants_count', 'views_count']


class JobListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = ['id', 'title', 'company_name', 'location', 'job_type',
                  'experience_required', 'salary_min', 'salary_max', 'status',
                  'applicants_count', 'created_at']


class ApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = '__all__'
        read_only_fields = ['candidate', 'ai_match_score', 'status']


class JobRecommendationSerializer(serializers.ModelSerializer):
    job = JobListSerializer(read_only=True)
    class Meta:
        model = JobRecommendation
        fields = '__all__'
