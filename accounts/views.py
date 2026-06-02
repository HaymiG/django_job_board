from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.db.models import Count, Q

from jobs.models import Application, Job

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
    """Login view with role-aware redirect."""
    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True
    
    def get_success_url(self):
        """Redirect to next page or role-specific dashboard on login."""
        # If 'next' parameter provided, use it
        next_page = self.request.GET.get('next')
        if next_page:
            return next_page
        
        # Default redirect by role
        if self.request.user.role == 'employer':
            return reverse_lazy('accounts:employer_dashboard')
        else:
            return reverse_lazy('accounts:job_seeker_dashboard')


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
    """Dashboard for employers - view posted jobs and applications."""
    company = getattr(request.user, "company", None)
    
    # Get job statistics
    jobs = []
    total_applications = 0
    pending_applications = 0
    
    if company:
        jobs = company.jobs.all()
        # Count total applications for this employer's jobs
        total_applications = Application.objects.filter(
            job__company=company
        ).count()
        # Count pending/reviewing applications
        pending_applications = Application.objects.filter(
            job__company=company,
            status__in=['submitted', 'reviewing']
        ).count()
    
    context = {
        "company": company,
        "jobs": jobs,
        "stats": {
            "posted_jobs": len(jobs),
            "total_applications": total_applications,
            "pending_applications": pending_applications,
        }
    }
    return render(request, "accounts/employer_dashboard.html", context)


@job_seeker_required
def job_seeker_dashboard(request):
    """Dashboard for job seekers - view applications and saved jobs."""
    all_applications = request.user.applications.select_related(
        "job", "job__company"
    ).order_by('-created_at')
    
    # Calculate stats
    stats = {
        "total_applications": all_applications.count(),
        "pending": all_applications.filter(status='submitted').count(),
        "reviewing": all_applications.filter(status='reviewing').count(),
        "accepted": all_applications.filter(status='accepted').count(),
        "rejected": all_applications.filter(status='rejected').count(),
    }
    
    # Limit to 15 most recent for display
    applications = all_applications[:15]
    
    context = {
        "applications": applications,
        "stats": stats,
    }
    return render(request, "accounts/job_seeker_dashboard.html", context)
