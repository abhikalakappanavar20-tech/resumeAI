from django.shortcuts import render


def home(request):
    context = {
        'total_users': 0,
        'total_jobs': 0,
        'total_resumes': 0,
    }
    return render(request, 'home.html', context)
