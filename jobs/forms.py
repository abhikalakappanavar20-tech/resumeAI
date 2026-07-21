from django import forms
from .models import Job, Application


class JobForm(forms.ModelForm):
    required_skills_text = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Python, Django, SQL (comma separated)'}),
        required=False, label='Required Skills'
    )
    preferred_skills_text = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Docker, AWS (comma separated)'}),
        required=False, label='Preferred Skills'
    )

    class Meta:
        model = Job
        fields = ['title', 'description', 'location', 'job_type', 'experience_required',
                  'salary_min', 'salary_max', 'requirements', 'responsibilities', 'benefits', 'deadline']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'job_type': forms.Select(attrs={'class': 'form-select'}),
            'experience_required': forms.Select(attrs={'class': 'form-select'}),
            'salary_min': forms.NumberInput(attrs={'class': 'form-control'}),
            'salary_max': forms.NumberInput(attrs={'class': 'form-control'}),
            'requirements': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'responsibilities': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'benefits': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'deadline': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def save(self, commit=True):
        job = super().save(commit=commit)
        req_skills = self.cleaned_data.get('required_skills_text', '')
        pref_skills = self.cleaned_data.get('preferred_skills_text', '')
        if req_skills:
            job.required_skills = [s.strip() for s in req_skills.split(',') if s.strip()]
        if pref_skills:
            job.preferred_skills = [s.strip() for s in pref_skills.split(',') if s.strip()]
        if commit:
            job.save()
        return job


class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['cover_letter', 'resume']
        widgets = {
            'cover_letter': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Write a brief cover letter...'}),
            'resume': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            from resumes.models import Resume
            self.fields['resume'].queryset = Resume.objects.filter(user=user)
