import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from resumes.models import Resume, ExtractedResumeData, ATSScore, CoverLetter, InterviewQuestion, SkillGap, ResumeImprovement
from jobs.models import Job, JobRecommendation
from .parser import parse_resume
from .scoring import calculate_ats_score
from .ai_services import (generate_cover_letter, generate_interview_questions,
                          generate_improvements, analyze_skill_gap, match_jobs)


@login_required
def analyze_resume(request, pk):
    """Analyze a resume: parse, extract data, calculate ATS score."""
    resume = get_object_or_404(Resume, pk=pk, user=request.user)
    resume.status = 'parsing'
    resume.save(update_fields=['status'])
    
    try:
        file_path = resume.file.path
        extracted, raw_text = parse_resume(file_path)
        
        if extracted is None:
            resume.status = 'error'
            resume.save(update_fields=['status'])
            messages.error(request, f'Failed to parse resume: {raw_text}')
            return redirect('resumes:resume_detail', pk=pk)
        
        resume.raw_text = raw_text
        resume.status = 'parsed'
        resume.save(update_fields=['raw_text', 'status'])
        
        extracted_data, _ = ExtractedResumeData.objects.update_or_create(
            resume=resume,
            defaults={
                'name': extracted.get('name', ''),
                'email': extracted.get('email', ''),
                'phone': extracted.get('phone', ''),
                'linkedin_url': extracted.get('linkedin_url', ''),
                'github_url': extracted.get('github_url', ''),
                'portfolio_url': extracted.get('portfolio_url', ''),
                'summary': extracted.get('summary', ''),
                'skills': extracted.get('skills', []),
                'education': extracted.get('education', []),
                'experience': extracted.get('experience', []),
                'projects': extracted.get('projects', []),
                'certifications': extracted.get('certifications', []),
            }
        )
        
        scores = calculate_ats_score(extracted, raw_text=raw_text)
        ats_score, _ = ATSScore.objects.update_or_create(
            resume=resume,
            defaults={
                'overall_score': scores['overall_score'],
                'formatting_score': scores['formatting_score'],
                'skills_match_score': scores['skills_match_score'],
                'experience_score': scores['experience_score'],
                'education_score': scores['education_score'],
                'keywords_score': scores['keywords_score'],
                'projects_score': scores['projects_score'],
                'suggestions': scores.get('suggestions', []),
                'missing_keywords': scores.get('missing_keywords', []),
            }
        )
        
        resume.status = 'analyzed'
        resume.save(update_fields=['status'])
        messages.success(request, 'Resume analyzed successfully!')
        
    except Exception as e:
        resume.status = 'error'
        resume.save(update_fields=['status'])
        messages.error(request, f'Error analyzing resume: {str(e)}')
    
    return redirect('resumes:resume_detail', pk=pk)


@login_required
def generate_cover_letter_view(request, pk):
    """Generate AI cover letter for a resume."""
    resume = get_object_or_404(Resume, pk=pk, user=request.user)
    
    if request.method == 'POST':
        company = request.POST.get('company', '')
        role = request.POST.get('role', '')
        job_description = request.POST.get('job_description', '')
        tone = request.POST.get('tone', 'professional')
        
        try:
            extracted_data = resume.extracted_data
            data = {
                'skills': extracted_data.skills,
                'experience': extracted_data.experience,
                'summary': extracted_data.summary,
                'education': extracted_data.education,
                'name': extracted_data.name,
            }
        except ExtractedResumeData.DoesNotExist:
            data = {'skills': [], 'experience': [], 'summary': '', 'education': [], 'name': ''}
        
        content = generate_cover_letter(data, company, role, job_description)
        
        cover_letter = CoverLetter.objects.create(
            resume=resume,
            company_name=company,
            job_title=role,
            content=content,
            tone=tone,
        )
        messages.success(request, 'Cover letter generated successfully!')
        return redirect('resumes:resume_detail', pk=pk)
    
    return redirect('resumes:resume_detail', pk=pk)


@login_required
def generate_interview_questions_view(request, pk):
    """Generate AI interview questions for a resume."""
    resume = get_object_or_404(Resume, pk=pk, user=request.user)

    if request.method != 'POST':
        return redirect('resumes:resume_detail', pk=pk)

    try:
        extracted_data = resume.extracted_data
        data = {'skills': extracted_data.skills}
    except ExtractedResumeData.DoesNotExist:
        data = {'skills': []}

    try:
        questions = generate_interview_questions(data)
        for q in questions:
            InterviewQuestion.objects.create(
                resume=resume,
                skill=q.get('skill', 'General'),
                question=q.get('question', ''),
                difficulty=q.get('difficulty', 'medium'),
                category=q.get('category', 'technical'),
            )
        messages.success(request, f'Generated {len(questions)} interview questions!')
    except Exception as e:
        messages.error(request, f'Error generating questions: {str(e)}')

    return redirect('resumes:resume_detail', pk=pk)


@login_required
def generate_improvements_view(request, pk):
    """Generate AI resume improvement suggestions."""
    resume = get_object_or_404(Resume, pk=pk, user=request.user)

    if request.method != 'POST':
        return redirect('resumes:resume_detail', pk=pk)

    try:
        extracted_data = resume.extracted_data
        data = {
            'skills': extracted_data.skills,
            'experience': extracted_data.experience,
            'summary': extracted_data.summary,
        }
        result = generate_improvements(data, resume.raw_text)
        
        improvements_list = result.get('improvements', []) if isinstance(result, dict) else (result if isinstance(result, list) else [])
        
        for imp in improvements_list:
            if isinstance(imp, dict):
                improved_val = imp.get('improved', imp.get('improved_text', ''))
                if isinstance(improved_val, dict):
                    improved_val = str(improved_val)
                original_val = imp.get('original', imp.get('original_text', ''))
                if isinstance(original_val, dict):
                    original_val = str(original_val)
                ResumeImprovement.objects.create(
                    resume=resume,
                    section=imp.get('section', ''),
                    original_text=str(original_val),
                    improved_text=str(improved_val),
                    explanation=imp.get('explanation', ''),
                )
        messages.success(request, 'Improvement suggestions generated!')
    except Exception as e:
        messages.error(request, f'Error generating improvements: {str(e)}')
    
    return redirect('resumes:resume_detail', pk=pk)


@login_required
def skill_gap_analysis_view(request, pk):
    """Generate AI skill gap analysis."""
    resume = get_object_or_404(Resume, pk=pk, user=request.user)

    if request.method != 'POST':
        return redirect('resumes:resume_detail', pk=pk)

    target_role = request.POST.get('target_role', '')

    if not target_role:
        messages.error(request, 'Please enter a target role.')
        return redirect('resumes:resume_detail', pk=pk)

    try:
        extracted_data = resume.extracted_data
        data = {
            'skills': extracted_data.skills,
            'experience': extracted_data.experience,
        }
        result = analyze_skill_gap(data, target_role)

        raw_missing = result.get('missing_skills', [])
        missing_skills = []
        for s in raw_missing:
            if isinstance(s, dict):
                if 'skill' in s:
                    missing_skills.append(s['skill'])
                elif 'skills_needed' in s:
                    missing_skills.extend(s['skills_needed'] if isinstance(s['skills_needed'], list) else [s['skills_needed']])
                elif 'name' in s:
                    missing_skills.append(s['name'])
            elif isinstance(s, str):
                missing_skills.append(s)

        raw_recs = result.get('recommendations', [])
        recommendations = []
        for r_item in raw_recs:
            if isinstance(r_item, dict):
                recommendations.append(r_item.get('recommendation', r_item.get('text', str(r_item))))
            elif isinstance(r_item, str):
                recommendations.append(r_item)

        SkillGap.objects.create(
            resume=resume,
            target_role=target_role,
            current_skills=extracted_data.skills,
            missing_skills=missing_skills,
            recommendations=recommendations,
            learning_roadmap=result.get('learning_roadmap', []),
            match_percentage=round(
                (len(extracted_data.skills) / max(len(missing_skills) + len(extracted_data.skills), 1)) * 100,
                1
            ),
        )
        messages.success(request, 'Skill gap analysis complete!')
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')

    return redirect('resumes:resume_detail', pk=pk)


@login_required
def job_recommendations_view(request, pk):
    """Get job recommendations for a resume."""
    resume = get_object_or_404(Resume, pk=pk, user=request.user)
    
    try:
        extracted_data = resume.extracted_data
        data = {
            'skills': extracted_data.skills,
            'experience': extracted_data.experience,
        }
    except ExtractedResumeData.DoesNotExist:
        data = {'skills': [], 'experience': []}
    
    active_jobs = Job.objects.filter(status='active')
    recommendations = match_jobs(data, active_jobs)
    
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
    
    context = {
        'resume': resume,
        'recommendations': recommendations[:20],
    }
    return render(request, 'ai_engine/job_recommendations.html', context)


@login_required
def analyze_resume_api(request, pk):
    """API endpoint to trigger resume analysis (AJAX)."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    resume = get_object_or_404(Resume, pk=pk, user=request.user)
    
    try:
        file_path = resume.file.path
        extracted, raw_text = parse_resume(file_path)
        
        if extracted is None:
            return JsonResponse({'error': 'Failed to parse resume'}, status=400)
        
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
                'linkedin_url': extracted.get('linkedin_url', ''),
                'github_url': extracted.get('github_url', ''),
            }
        )
        
        scores = calculate_ats_score(extracted, raw_text=raw_text)
        ATSScore.objects.update_or_create(
            resume=resume,
            defaults={
                'overall_score': scores['overall_score'],
                'formatting_score': scores['formatting_score'],
                'skills_match_score': scores['skills_match_score'],
                'experience_score': scores['experience_score'],
                'education_score': scores['education_score'],
                'keywords_score': scores['keywords_score'],
                'projects_score': scores['projects_score'],
                'suggestions': scores.get('suggestions', []),
                'missing_keywords': scores.get('missing_keywords', []),
            }
        )
        
        resume.status = 'analyzed'
        resume.save(update_fields=['status'])
        
        return JsonResponse({
            'status': 'success',
            'ats_score': scores['overall_score'],
            'skills_count': len(extracted.get('skills', [])),
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
