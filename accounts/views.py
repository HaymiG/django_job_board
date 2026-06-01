from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy

from .decorators import employer_required, job_seeker_required
from .forms import LoginForm, ProfileForm, RegistrationForm
def register(request):
    if request.user.is_authenticated:
        return redirect("accounts:profile")

    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Welcome! Your account has been created.")
            return redirect("accounts:profile")
    else:
        form = RegistrationForm()

    return render(request, "accounts/register.html", {"form": form})


class UserLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True


class UserLogoutView(LogoutView):
    next_page = reverse_lazy("jobs:home")


@login_required
def profile(request):
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect("accounts:profile")
    else:
        form = ProfileForm(instance=request.user)

    return render(
        request,
        "accounts/profile.html",
        {
            "form": form,
            "role_display": request.user.get_role_display(),
        },
    )


@employer_required
def employer_dashboard(request):
    company = getattr(request.user, "company", None)
    return render(
        request,
        "accounts/employer_dashboard.html",
        {"company": company},
    )


@job_seeker_required
def job_seeker_dashboard(request):
    applications = request.user.applications.select_related("job", "job__company")[:10]
    return render(
        request,
        "accounts/job_seeker_dashboard.html",
        {"applications": applications},
    )
