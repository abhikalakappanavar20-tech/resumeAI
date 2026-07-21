from django import forms
from .models import Resume


class ResumeUploadForm(forms.ModelForm):
    file = forms.FileField(widget=forms.FileInput(attrs={
        'class': 'form-control',
        'accept': '.pdf,.docx,.doc'
    }))

    class Meta:
        model = Resume
        fields = ['title', 'file']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Resume Title'}),
        }

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            ext = file.name.split('.')[-1].lower()
            if ext not in ['pdf', 'docx', 'doc']:
                raise forms.ValidationError('Only PDF and DOCX files are allowed.')
            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError('File size must be under 10MB.')
        return file
