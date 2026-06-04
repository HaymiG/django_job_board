from django import forms

from .models import Application, Job


class ApplicationForm(forms.ModelForm):
    """Form for job seekers to apply to a job posting."""

    class Meta:
        model = Application
        fields = ("cover_letter", "resume")
        widgets = {
            "cover_letter": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": "Tell the employer why you're a great fit for this role…",
                }
            ),
            "resume": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                    "accept": ".pdf",
                }
            ),
        }
        labels = {
            "cover_letter": "Cover letter",
            "resume": "Resume (PDF)",
        }
        help_texts = {
            "resume": "Upload your resume as a PDF file (max 5 MB).",
        }

    def clean_resume(self):
        """Validate the uploaded resume is a PDF and under 5 MB."""
        resume = self.cleaned_data.get("resume")
        if resume:
            # Check file extension
            if not resume.name.lower().endswith(".pdf"):
                raise forms.ValidationError("Only PDF files are accepted.")
            # Check file size (5 MB limit)
            max_size = 5 * 1024 * 1024
            if resume.size > max_size:
                raise forms.ValidationError(
                    "File size must be under 5 MB."
                )
        return resume


class JobForm(forms.ModelForm):
    """Form for creating and editing job postings."""

    description = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 8,
                "placeholder": "Describe the job role, responsibilities, and requirements...",
            }
        )
    )

    class Meta:
        model = Job
        fields = (
            "title",
            "description",
            "location",
            "job_type",
            "category",
            "salary_min",
            "salary_max",
            "salary_currency",
        )
        widgets = {
            "title": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Job Title"}
            ),
            "location": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Location"}
            ),
            "job_type": forms.Select(attrs={"class": "form-select"}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "salary_min": forms.NumberInput(
                attrs={"class": "form-control", "placeholder": "Minimum salary (optional)"}
            ),
            "salary_max": forms.NumberInput(
                attrs={"class": "form-control", "placeholder": "Maximum salary (optional)"}
            ),
            "salary_currency": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        """Make salary_currency optional if no salary is entered."""
        super().__init__(*args, **kwargs)
        self.fields["salary_currency"].required = False

    def clean(self):
        """Validate that salary_min <= salary_max."""
        cleaned_data = super().clean()
        salary_min = cleaned_data.get("salary_min")
        salary_max = cleaned_data.get("salary_max")

        if salary_min and salary_max and salary_min > salary_max:
            raise forms.ValidationError(
                "Minimum salary cannot exceed maximum salary."
            )
        return cleaned_data
