from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from accounts.models import User, CandidateProfile
from resumes.models import Resume, ATSScore
from jobs.models import Job, Application
from .models import CandidateShortlist, CandidateSearch


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
    
    ranked = []
    for app in applications:
        resume = app.resume
        ats_score = None
        if resume:
            try:
                ats_score = resume.ats_score
            except ATSScore.DoesNotExist:
                pass
        
        ranked.append({
            'application': app,
            'candidate': app.candidate,
            'ats_score': ats_score.overall_score if ats_score else 0,
            'match_score': app.ai_match_score,
        })
    
    ranked.sort(key=lambda x: x['match_score'], reverse=True)
    
    context = {'job': job, 'ranked_candidates': ranked}
    return render(request, 'recruiter/rank_candidates.html', context)
