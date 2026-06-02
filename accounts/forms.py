from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import User, UserRole


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "you@example.com"}),
    )
    role = forms.ChoiceField(
        choices=UserRole.choices,
        widget=forms.RadioSelect,
        label="I am a",
    )

    class Meta:
        model = User
        fields = ("username", "email", "role", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ("username", "password1", "password2"):
            self.fields[name].widget.attrs.update({"class": "form-control"})
        self.fields["username"].widget.attrs["placeholder"] = "Choose a username"

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.role = self.cleaned_data["role"]
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Username"}
        )
        self.fields["password"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Password"}
        )


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")
        widgets = {
            "first_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "John"
            }),
            "last_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Doe"
            }),
            "email": forms.EmailInput(attrs={
                "class": "form-control",
                "placeholder": "john@example.com"
            }),
        }
    
    def clean_email(self):
        """Validate email is unique among non-current user"""
        email = self.cleaned_data.get('email')
        if email:
            # Check if email already exists for another user
            user_with_email = User.objects.filter(email=email).exclude(pk=self.instance.pk).first()
            if user_with_email:
                raise forms.ValidationError(
                    'A user with this email address already exists.',
                    code='email_exists'
                )
        return email
