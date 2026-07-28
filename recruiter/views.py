from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from accounts.models import User, CandidateProfile
from resumes.models import Resume, ATSScore, ExtractedResumeData
from jobs.models import Job, Application
from .models import CandidateShortlist, CandidateSearch
from ai_engine.ai_services import rank_candidates as ai_rank_candidates, is_ai_available


@login_required
def dashboard(request):
    if request.user.role != 'recruiter':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    jobs = Job.objects.filter(recruiter=request.user)
    total_applications = Application.objects.filter(job__recruiter=request.user).count()
    shortlisted = CandidateShortlist.objects.filter(recruiter=request.user).count()
    recent_applications = Application.objects.filter(job__recruiter=request.user).order_by('-applied_at')[:10]
    
    context = {
        'jobs': jobs,
        'total_applications': total_applications,
        'shortlisted': shortlisted,
        'recent_applications': recent_applications,
    }
    return render(request, 'recruiter/dashboard.html', context)


@login_required
def search_candidates(request):
    if request.user.role != 'recruiter':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    candidates = CandidateProfile.objects.all()
    query = request.GET.get('q', '')
    skill = request.GET.get('skill', '')
    experience = request.GET.get('experience', '')
    location = request.GET.get('location', '')
    
    results_count = 0
    
    if query:
        candidates = candidates.filter(
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(headline__icontains=query)
        )
    if skill:
        candidates = candidates.filter(skills__contains=[skill])
    if location:
        candidates = candidates.filter(location__icontains=location)
    if experience:
        try:
            candidates = candidates.filter(total_experience_years__gte=int(experience))
        except (ValueError, TypeError):
            pass
    
    results_count = candidates.count()
    
    if query or skill:
        CandidateSearch.objects.create(
            recruiter=request.user,
            query=query or skill,
            results_count=results_count
        )
    
    context = {
        'candidates': candidates,
        'query': query,
        'skill': skill,
        'location': location,
        'experience': experience,
        'results_count': results_count,
    }
    return render(request, 'recruiter/search_candidates.html', context)


@login_required
def candidate_profile(request, pk):
    if request.user.role != 'recruiter':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    candidate = get_object_or_404(User, pk=pk, role='candidate')
    profile = CandidateProfile.objects.filter(user=candidate).first()
    resumes = Resume.objects.filter(user=candidate)
    ats_scores = ATSScore.objects.filter(resume__user=candidate)
    is_shortlisted = CandidateShortlist.objects.filter(
        recruiter=request.user, candidate=candidate
    ).exists()
    
    context = {
        'candidate': candidate,
        'profile': profile,
        'resumes': resumes,
        'ats_scores': ats_scores,
        'is_shortlisted': is_shortlisted,
    }
    return render(request, 'recruiter/candidate_profile.html', context)


@login_required
def shortlist_candidate(request, pk):
    if request.user.role != 'recruiter':
        return redirect('home')
    
    candidate = get_object_or_404(User, pk=pk, role='candidate')
    shortlist, created = CandidateShortlist.objects.get_or_create(
        recruiter=request.user,
        candidate=candidate
    )
    if not created:
        shortlist.delete()
        messages.info(request, f'Removed {candidate.get_full_name()} from shortlist.')
    else:
        messages.success(request, f'Added {candidate.get_full_name()} to shortlist.')
    
    return redirect('recruiter:candidate_profile', pk=pk)


@login_required
def my_shortlist(request):
    if request.user.role != 'recruiter':
        return redirect('home')
    
    shortlisted = CandidateShortlist.objects.filter(recruiter=request.user).select_related('candidate', 'job')
    return render(request, 'recruiter/shortlist.html', {'shortlisted': shortlisted})


@login_required
def rank_candidates(request, job_pk):
    if request.user.role != 'recruiter':
        return redirect('home')

    job = get_object_or_404(Job, pk=job_pk, recruiter=request.user)
    applications = Application.objects.filter(job=job).select_related('candidate')

    candidates_data = []
    for app in applications:
        resume = app.resume
        ats_score = 0
        skills = []
        summary = ''
        if resume:
            try:
                ats_obj = resume.ats_score
                ats_score = ats_obj.overall_score if ats_obj else 0
            except ATSScore.DoesNotExist:
                pass
            try:
                extracted = resume.extracted_data
                skills = extracted.skills
                summary = extracted.summary
            except ExtractedResumeData.DoesNotExist:
                pass

        candidates_data.append({
            'user': app.candidate,
            'application': app,
            'ats_score': ats_score,
            'skills': skills,
            'summary': summary,
        })

    if is_ai_available() and candidates_data:
        ai_ranked = ai_rank_candidates(candidates_data, job)
        for item in ai_ranked:
            cand = item.get('candidate')
            for cd in candidates_data:
                if cd['user'] == cand:
                    item['application'] = cd['application']
                    break
        ranked = ai_ranked
    else:
        ranked = []
        for cd in candidates_data:
            ranked.append({
                'candidate': cd['user'],
                'application': cd['application'],
                'ats_score': cd['ats_score'],
                'match_score': cd['ats_score'],
                'matching_skills': cd['skills'][:5],
                'strengths': '',
                'weakness': '',
                'recommendation': 'moderate_fit',
            })
        ranked.sort(key=lambda x: x.get('match_score', 0), reverse=True)

    context = {
        'job': job,
        'ranked_candidates': ranked,
        'ai_powered': is_ai_available(),
    }
    return render(request, 'recruiter/rank_candidates.html', context)
