from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import (CandidateRegistrationForm, RecruiterRegistrationForm,
                    UserLoginForm, CandidateProfileForm, RecruiterProfileForm,
                    UserUpdateForm)
from .models import CandidateProfile, RecruiterProfile


def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    role = request.GET.get('role', 'candidate')

    if request.method == 'POST':
        if role == 'recruiter':
            form = RecruiterRegistrationForm(request.POST)
        else:
            form = CandidateRegistrationForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome {user.first_name}! Your account has been created.')
            if role == 'recruiter':
                return redirect('recruiter:dashboard')
            return redirect('resumes:dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        if role == 'recruiter':
            form = RecruiterRegistrationForm()
        else:
            form = CandidateRegistrationForm()

    return render(request, 'accounts/register.html', {
        'form': form, 'role': role
    })


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.first_name}!')
                next_url = request.GET.get('next', '')
                if next_url and next_url.startswith('/') and not next_url.startswith('//'):
                    return redirect(next_url)
                return redirect('home')
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = UserLoginForm()

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('home')


@login_required
def profile_view(request):
    user = request.user
    user_form = UserUpdateForm(instance=user)
    profile_form = None
    profile = None

    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, request.FILES, instance=user)
        user_valid = user_form.is_valid()
        profile_valid = True

        if user.role == 'candidate':
            profile, _ = CandidateProfile.objects.get_or_create(user=user)
            profile_form = CandidateProfileForm(request.POST, instance=profile)
            profile_valid = profile_form.is_valid()
        elif user.role == 'recruiter':
            profile, _ = RecruiterProfile.objects.get_or_create(user=user)
            profile_form = RecruiterProfileForm(request.POST, request.FILES, instance=profile)
            profile_valid = profile_form.is_valid()

        if user_valid and profile_valid:
            user_form.save()
            if profile_form:
                profile_form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        if user.role == 'candidate':
            profile, _ = CandidateProfile.objects.get_or_create(user=user)
            profile_form = CandidateProfileForm(instance=profile)
        elif user.role == 'recruiter':
            profile, _ = RecruiterProfile.objects.get_or_create(user=user)
            profile_form = RecruiterProfileForm(instance=profile)

    context = {'user_form': user_form, 'user': user}
    if profile_form:
        context['profile_form'] = profile_form
    if profile:
        context['profile'] = profile

    return render(request, 'accounts/profile.html', context)
