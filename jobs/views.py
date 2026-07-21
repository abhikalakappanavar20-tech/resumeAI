from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Job, Application, JobRecommendation
from .forms import JobForm, ApplicationForm


@login_required
def job_list(request):
    jobs = Job.objects.filter(status='active')
    query = request.GET.get('q', '')
    job_type = request.GET.get('type', '')
    location = request.GET.get('location', '')
    experience = request.GET.get('experience', '')
    
    if query:
        jobs = jobs.filter(Q(title__icontains=query) | Q(description__icontains=query) | Q(company_name__icontains=query))
    if job_type:
        jobs = jobs.filter(job_type=job_type)
    if location:
        jobs = jobs.filter(location__icontains=location)
    if experience:
        jobs = jobs.filter(experience_required=experience)
    
    context = {
        'jobs': jobs,
        'query': query,
        'job_type': job_type,
        'location': location,
        'experience': experience,
    }
    return render(request, 'jobs/job_list.html', context)


@login_required
def job_detail(request, pk):
    job = get_object_or_404(Job, pk=pk)
    job.views_count += 1
    job.save(update_fields=['views_count'])
    has_applied = Application.objects.filter(job=job, candidate=request.user).exists()
    similar_jobs = Job.objects.filter(status='active').exclude(pk=pk)[:5]
    # Filter similar by matching skills or same company
    if job.required_skills:
        similar_jobs = Job.objects.filter(
            Q(required_skills__overlap=job.required_skills) | Q(company_name=job.company_name),
            status='active'
        ).exclude(pk=pk)[:5]
    context = {
        'job': job,
        'has_applied': has_applied,
        'similar_jobs': similar_jobs,
    }
    return render(request, 'jobs/job_detail.html', context)


@login_required
def create_job(request):
    if request.user.role != 'recruiter':
        messages.error(request, 'Only recruiters can post jobs.')
        return redirect('jobs:job_list')
    
    if request.method == 'POST':
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.recruiter = request.user
            job.company_name = request.user.recruiter_profile.company_name
            job.save()
            messages.success(request, 'Job posted successfully!')
            return redirect('jobs:job_detail', pk=job.pk)
    else:
        form = JobForm()
    return render(request, 'jobs/create_job.html', {'form': form})


@login_required
def edit_job(request, pk):
    job = get_object_or_404(Job, pk=pk, recruiter=request.user)
    if request.method == 'POST':
        form = JobForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            messages.success(request, 'Job updated successfully!')
            return redirect('jobs:job_detail', pk=job.pk)
    else:
        form = JobForm(instance=job)
    return render(request, 'jobs/edit_job.html', {'form': form, 'job': job})


@login_required
def delete_job(request, pk):
    job = get_object_or_404(Job, pk=pk, recruiter=request.user)
    if request.method == 'POST':
        job.delete()
        messages.success(request, 'Job deleted successfully.')
        return redirect('jobs:my_jobs')
    return render(request, 'jobs/delete_confirm.html', {'job': job})


@login_required
def apply_job(request, pk):
    job = get_object_or_404(Job, pk=pk)
    if request.user.role != 'candidate':
        messages.error(request, 'Only candidates can apply for jobs.')
        return redirect('jobs:job_detail', pk=pk)
    
    if Application.objects.filter(job=job, candidate=request.user).exists():
        messages.warning(request, 'You have already applied for this job.')
        return redirect('jobs:job_detail', pk=pk)
    
    if request.method == 'POST':
        form = ApplicationForm(request.POST, user=request.user)
        if form.is_valid():
            application = form.save(commit=False)
            application.job = job
            application.candidate = request.user
            application.save()
            job.applicants_count += 1
            job.save(update_fields=['applicants_count'])
            messages.success(request, 'Application submitted successfully!')
            return redirect('jobs:job_detail', pk=pk)
    else:
        form = ApplicationForm(user=request.user)
    return render(request, 'jobs/apply.html', {'form': form, 'job': job})


@login_required
def my_applications(request):
    applications = Application.objects.filter(candidate=request.user)
    return render(request, 'jobs/my_applications.html', {'applications': applications})


@login_required
def my_jobs(request):
    if request.user.role != 'recruiter':
        return redirect('jobs:job_list')
    jobs = Job.objects.filter(recruiter=request.user)
    return render(request, 'jobs/my_jobs.html', {'jobs': jobs})


@login_required
def job_applications(request, pk):
    job = get_object_or_404(Job, pk=pk, recruiter=request.user)
    applications = Application.objects.filter(job=job).order_by('-ai_match_score')
    return render(request, 'jobs/job_applications.html', {'job': job, 'applications': applications})
