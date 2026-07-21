from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import (Resume, ExtractedResumeData, ATSScore, CoverLetter,
                     InterviewQuestion, SkillGap, Skill)
from .forms import ResumeUploadForm


@login_required
def dashboard(request):
    resumes = Resume.objects.filter(user=request.user)
    total_resumes = resumes.count()
    analyzed_count = resumes.filter(status='analyzed').count()
    avg_score = 0
    ats_scores = ATSScore.objects.filter(resume__user=request.user)
    if ats_scores.exists():
        avg_score = sum(s.overall_score for s in ats_scores) / ats_scores.count()
    context = {
        'resumes': resumes[:5],
        'total_resumes': total_resumes,
        'analyzed_count': analyzed_count,
        'avg_score': round(avg_score, 1),
    }
    return render(request, 'resumes/dashboard.html', context)


@login_required
def upload_resume(request):
    if request.method == 'POST':
        form = ResumeUploadForm(request.POST, request.FILES)
        if form.is_valid():
            resume = form.save(commit=False)
            resume.user = request.user
            resume.file_type = resume.file.name.split('.')[-1].lower()
            resume.file_size = resume.file.size
            resume.save()
            messages.success(request, 'Resume uploaded successfully! Processing...')
            return redirect('resumes:resume_detail', pk=resume.pk)
    else:
        form = ResumeUploadForm()
    return render(request, 'resumes/upload.html', {'form': form})


@login_required
def resume_detail(request, pk):
    resume = get_object_or_404(Resume, pk=pk, user=request.user)
    extracted_data = None
    ats_score = None
    cover_letters = CoverLetter.objects.filter(resume=resume)
    interview_questions = InterviewQuestion.objects.filter(resume=resume)
    skill_gaps = SkillGap.objects.filter(resume=resume)
    improvements = resume.improvements.all()

    try:
        extracted_data = resume.extracted_data
    except ExtractedResumeData.DoesNotExist:
        pass

    try:
        ats_score = resume.ats_score
    except ATSScore.DoesNotExist:
        pass

    context = {
        'resume': resume,
        'extracted_data': extracted_data,
        'ats_score': ats_score,
        'cover_letters': cover_letters,
        'interview_questions': interview_questions,
        'skill_gaps': skill_gaps,
        'improvements': improvements,
    }
    return render(request, 'resumes/detail.html', context)


@login_required
def delete_resume(request, pk):
    resume = get_object_or_404(Resume, pk=pk, user=request.user)
    if request.method == 'POST':
        resume.file.delete()
        resume.delete()
        messages.success(request, 'Resume deleted successfully.')
        return redirect('resumes:dashboard')
    return render(request, 'resumes/delete_confirm.html', {'resume': resume})


@login_required
def resume_history(request):
    resumes = Resume.objects.filter(user=request.user)
    return render(request, 'resumes/history.html', {'resumes': resumes})
