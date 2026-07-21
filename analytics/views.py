from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count, Avg, Sum
from django.utils import timezone
from datetime import timedelta
from accounts.models import User
from resumes.models import Resume, ATSScore
from jobs.models import Job, Application
from .models import AIUsageLog, PlatformAnalytics


def is_admin(user):
    return user.is_authenticated and (user.is_superuser or user.role == 'admin')


@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    from datetime import date
    
    total_users = User.objects.count()
    total_candidates = User.objects.filter(role='candidate').count()
    total_recruiters = User.objects.filter(role='recruiter').count()
    total_resumes = Resume.objects.count()
    total_jobs = Job.objects.count()
    total_applications = Application.objects.count()
    total_ai_requests = AIUsageLog.objects.count()
    
    avg_ats = 0
    ats_scores = ATSScore.objects.aggregate(avg=Avg('overall_score'))
    if ats_scores['avg']:
        avg_ats = round(ats_scores['avg'], 1)
    
    recent_users = User.objects.all().order_by('-date_joined')[:10]
    recent_applications = Application.objects.all().order_by('-applied_at')[:10]
    
    today = date.today()
    weekly_registrations = User.objects.filter(
        date_joined__gte=today - timedelta(days=7)
    ).count()
    weekly_applications = Application.objects.filter(
        applied_at__gte=today - timedelta(days=7)
    ).count()
    
    ai_usage_stats = AIUsageLog.objects.values('feature').annotate(
        count=Count('id'),
        total_tokens=Sum('tokens_used')
    ).order_by('-count')
    
    context = {
        'total_users': total_users,
        'total_candidates': total_candidates,
        'total_recruiters': total_recruiters,
        'total_resumes': total_resumes,
        'total_jobs': total_jobs,
        'total_applications': total_applications,
        'total_ai_requests': total_ai_requests,
        'avg_ats': avg_ats,
        'recent_users': recent_users,
        'recent_applications': recent_applications,
        'weekly_registrations': weekly_registrations,
        'weekly_applications': weekly_applications,
        'ai_usage_stats': ai_usage_stats,
    }
    return render(request, 'analytics/dashboard.html', context)


@login_required
@user_passes_test(is_admin)
def manage_users(request):
    users = User.objects.all().order_by('-date_joined')
    role_filter = request.GET.get('role', '')
    if role_filter:
        users = users.filter(role=role_filter)
    
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        action = request.POST.get('action')
        try:
            target_user = User.objects.get(pk=user_id)
        except (User.DoesNotExist, ValueError, TypeError):
            messages.error(request, 'Invalid user.')
            return redirect('analytics:manage_users')
        if action == 'toggle_active':
            target_user.is_active = not target_user.is_active
            target_user.save()
            messages.success(request, f'User {target_user.username} {"activated" if target_user.is_active else "deactivated"}.')
        elif action == 'change_role':
            new_role = request.POST.get('new_role')
            target_user.role = new_role
            target_user.save()
            messages.success(request, f'User {target_user.username} role changed to {new_role}.')
    
    context = {'users': users, 'role_filter': role_filter}
    return render(request, 'analytics/manage_users.html', context)


@login_required
@user_passes_test(is_admin)
def manage_jobs(request):
    jobs = Job.objects.all().order_by('-created_at')
    status_filter = request.GET.get('status', '')
    if status_filter:
        jobs = jobs.filter(status=status_filter)
    context = {'jobs': jobs, 'status_filter': status_filter}
    return render(request, 'analytics/manage_jobs.html', context)


@login_required
@user_passes_test(is_admin)
def ai_usage_report(request):
    logs = AIUsageLog.objects.all()
    
    feature_stats = logs.values('feature').annotate(
        count=Count('id'),
        total_tokens=Sum('tokens_used'),
        avg_response=Avg('response_time_ms')
    ).order_by('-count')
    
    daily_usage = logs.filter(
        created_at__gte=timezone.now() - timedelta(days=30)
    ).extra(
        select={'date': "date(created_at)"}
    ).values('date').annotate(count=Count('id')).order_by('date')
    
    context = {
        'feature_stats': feature_stats,
        'daily_usage': daily_usage,
        'total_requests': logs.count(),
        'total_tokens': logs.aggregate(total=Sum('tokens_used'))['total'] or 0,
    }
    return render(request, 'analytics/ai_usage.html', context)
