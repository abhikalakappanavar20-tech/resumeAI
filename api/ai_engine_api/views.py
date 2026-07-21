import json
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from resumes.models import Resume, ExtractedResumeData, ATSScore, CoverLetter, InterviewQuestion, SkillGap, ResumeImprovement
from jobs.models import Job, JobRecommendation
from ai_engine.parser import parse_resume
from ai_engine.scoring import calculate_ats_score
from ai_engine.ai_services import (generate_cover_letter, generate_interview_questions,
                                    generate_improvements, analyze_skill_gap, match_jobs)
from .serializers import CoverLetterRequestSerializer, SkillGapRequestSerializer


class AnalyzeResumeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            resume = Resume.objects.get(pk=pk, user=request.user)
        except Resume.DoesNotExist:
            return Response({"error": "Resume not found"}, status=status.HTTP_404_NOT_FOUND)
        
        file_path = resume.file.path
        extracted, raw_text = parse_resume(file_path)
        
        if extracted is None:
            return Response({"error": "Failed to parse resume"}, status=status.HTTP_400_BAD_REQUEST)
        
        resume.raw_text = raw_text
        resume.status = 'parsed'
        resume.save(update_fields=['raw_text', 'status'])
        
        ExtractedResumeData.objects.update_or_create(
            resume=resume,
            defaults={
                'name': extracted.get('name', ''),
                'email': extracted.get('email', ''),
                'phone': extracted.get('phone', ''),
                'skills': extracted.get('skills', []),
                'education': extracted.get('education', []),
                'experience': extracted.get('experience', []),
                'projects': extracted.get('projects', []),
                'certifications': extracted.get('certifications', []),
                'summary': extracted.get('summary', ''),
            }
        )
        
        scores = calculate_ats_score(extracted, raw_text=raw_text)
        ATSScore.objects.update_or_create(
            resume=resume,
            defaults=scores
        )
        
        resume.status = 'analyzed'
        resume.save(update_fields=['status'])
        
        return Response({
            "status": "success",
            "ats_score": scores['overall_score'],
            "skills_count": len(extracted.get('skills', [])),
            "suggestions": scores.get('suggestions', []),
        })


class GenerateCoverLetterView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        serializer = CoverLetterRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            resume = Resume.objects.get(pk=pk, user=request.user)
        except Resume.DoesNotExist:
            return Response({"error": "Resume not found"}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            data = {
                'skills': resume.extracted_data.skills,
                'experience': resume.extracted_data.experience,
                'summary': resume.extracted_data.summary,
            }
        except ExtractedResumeData.DoesNotExist:
            data = {'skills': [], 'experience': [], 'summary': ''}
        
        content = generate_cover_letter(
            data,
            serializer.validated_data['company'],
            serializer.validated_data['role'],
            serializer.validated_data.get('job_description', '')
        )
        
        cover_letter = CoverLetter.objects.create(
            resume=resume,
            company_name=serializer.validated_data['company'],
            job_title=serializer.validated_data['role'],
            content=content,
        )
        
        return Response({
            "cover_letter": content,
            "id": str(cover_letter.id),
        })


class GenerateInterviewQuestionsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            resume = Resume.objects.get(pk=pk, user=request.user)
        except Resume.DoesNotExist:
            return Response({"error": "Resume not found"}, status=status.HTTP_404_NOT_FOUND)
        
        skills = request.data.get('skills', [])
        if not skills:
            try:
                skills = resume.extracted_data.skills
            except ExtractedResumeData.DoesNotExist:
                pass
        
        questions = generate_interview_questions({'skills': skills})
        
        for q in questions:
            InterviewQuestion.objects.create(
                resume=resume,
                skill=q.get('skill', 'General'),
                question=q.get('question', ''),
                difficulty=q.get('difficulty', 'medium'),
                category=q.get('category', 'technical'),
            )
        
        return Response({"questions": questions})


class SkillGapAnalysisView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        serializer = SkillGapRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            resume = Resume.objects.get(pk=pk, user=request.user)
        except Resume.DoesNotExist:
            return Response({"error": "Resume not found"}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            data = {
                'skills': resume.extracted_data.skills,
                'experience': resume.extracted_data.experience,
            }
        except ExtractedResumeData.DoesNotExist:
            data = {'skills': [], 'experience': []}
        
        result = analyze_skill_gap(data, serializer.validated_data['target_role'])
        
        skill_gap = SkillGap.objects.create(
            resume=resume,
            target_role=serializer.validated_data['target_role'],
            current_skills=data.get('skills', []),
            missing_skills=[s['skill'] for s in result.get('missing_skills', [])],
            recommendations=result.get('recommendations', []),
            learning_roadmap=result.get('learning_roadmap', []),
        )
        
        return Response(result)


class JobRecommendationsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            resume = Resume.objects.get(pk=pk, user=request.user)
        except Resume.DoesNotExist:
            return Response({"error": "Resume not found"}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            data = {
                'skills': resume.extracted_data.skills,
                'experience': resume.extracted_data.experience,
            }
        except ExtractedResumeData.DoesNotExist:
            data = {'skills': [], 'experience': []}
        
        active_jobs = Job.objects.filter(status='active')
        recommendations = match_jobs(data, active_jobs)
        
        result = []
        for rec in recommendations[:20]:
            JobRecommendation.objects.update_or_create(
                candidate=request.user,
                job=rec['job'],
                defaults={
                    'match_score': rec['match_score'],
                    'matching_skills': rec['matching_skills'],
                    'missing_skills': rec['missing_skills'],
                }
            )
            result.append({
                'job_id': str(rec['job'].id),
                'title': rec['job'].title,
                'company': rec['job'].company_name,
                'match_score': rec['match_score'],
                'matching_skills': rec['matching_skills'],
                'missing_skills': rec['missing_skills'],
            })
        
        return Response({"recommendations": result})


class GenerateImprovementsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            resume = Resume.objects.get(pk=pk, user=request.user)
        except Resume.DoesNotExist:
            return Response({"error": "Resume not found"}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            data = {
                'skills': resume.extracted_data.skills,
                'experience': resume.extracted_data.experience,
                'summary': resume.extracted_data.summary,
            }
        except ExtractedResumeData.DoesNotExist:
            data = {'skills': [], 'experience': [], 'summary': ''}
        
        result = generate_improvements(data, resume.raw_text)
        
        for imp in result.get('improvements', []):
            ResumeImprovement.objects.create(
                resume=resume,
                section=imp.get('section', ''),
                original_text=imp.get('original', ''),
                improved_text=imp.get('improved', ''),
                explanation=imp.get('explanation', ''),
            )
        
        return Response(result)
