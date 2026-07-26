from django.shortcuts import render


def home(request):
    from accounts.models import User
    from jobs.models import Job
    from resumes.models import Resume

    context = {
        'total_users': User.objects.count(),
        'total_jobs': Job.objects.filter(status='active').count(),
        'total_resumes': Resume.objects.count(),
    }
    return render(request, 'home.html', context)
