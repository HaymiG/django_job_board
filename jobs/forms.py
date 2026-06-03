from django import forms

from .models import Job


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
