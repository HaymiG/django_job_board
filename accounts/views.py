from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.db.models import Count, Q, Sum, Avg

from jobs.emails import send_registration_confirmation
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
            send_registration_confirmation(user)  # send welcome email
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
    total_views = 0  # initialised here so it's always defined in context

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
        # Sum all job view counts
        from django.db.models import Sum as _Sum
        total_views = jobs.aggregate(tv=_Sum("views"))["tv"] or 0

    context = {
        "company": company,
        "jobs": jobs,
        "stats": {
            "posted_jobs": len(jobs),
            "total_applications": total_applications,
            "pending_applications": pending_applications,
            "total_views": total_views,
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


@employer_required
def employer_analytics(request):
    """
    Analytics dashboard for employers.

    Django aggregations used here:
    ─────────────────────────────
    annotate() adds a computed column to EVERY ROW of the QuerySet.
    Django translates it into a SQL expression added to the SELECT clause.

        Job.objects
        .annotate(
            application_count=Count("applications"),  # per-job count
            total_views=Sum("views"),                 # same as .views but via annotation
        )

        This is equivalent to:
        SELECT jobs_job.*, COUNT(jobs_application.id) AS application_count
        FROM jobs_job
        LEFT JOIN jobs_application ON jobs_application.job_id = jobs_job.id
        GROUP BY jobs_job.id

    aggregate() (used at the end) collapses the WHOLE QuerySet to one dict:
        Application.objects.aggregate(avg_per_job=Avg("job__applications__count"))
    """
    company = getattr(request.user, "company", None)
    if not company:
        messages.warning(request, "You need a company profile to view analytics.")
        return redirect("accounts:employer_dashboard")

    # ── Per-job stats using annotate() ────────────────────────────────────────
    # annotate() adds application_count as a computed column on each Job row.
    # Count("applications") uses the reverse FK name (related_name on Application.job)
    jobs_with_stats = (
        company.jobs.annotate(
            application_count=Count("applications"),
        )
        .order_by("-created_at")
    )

    # ── Application status breakdown using aggregate() ─────────────────────────
    # aggregate() returns a single dict with summary values across the whole QS
    app_qs = Application.objects.filter(job__company=company)
    status_counts = app_qs.aggregate(
        submitted=Count("id", filter=Q(status="submitted")),
        reviewing=Count("id", filter=Q(status="reviewing")),
        accepted=Count("id", filter=Q(status="accepted")),
        rejected=Count("id", filter=Q(status="rejected")),
    )

    # ── Top jobs by views ──────────────────────────────────────────────────────
    top_by_views = jobs_with_stats.order_by("-views")[:5]
    top_by_applications = jobs_with_stats.order_by("-application_count")[:5]

    # ── Total views across all company jobs ────────────────────────────────────
    totals = jobs_with_stats.aggregate(
        total_views=Sum("views"),
        total_applications=Sum("application_count"),
    )

    # ── Build Chart.js-ready data (lists of labels + values) ──────────────────
    # We serialize in Python so the template only needs {{ chart_data|safe }}
    import json

    # Bar chart: applications per job (top 8 for readability)
    top8 = jobs_with_stats.order_by("-application_count")[:8]
    applications_chart = json.dumps({
        "labels": [j.title for j in top8],
        "data":   [j.application_count for j in top8],
    })

    # Doughnut chart: application status breakdown
    status_chart = json.dumps({
        "labels": ["Submitted", "Reviewing", "Accepted", "Rejected"],
        "data": [
            status_counts["submitted"],
            status_counts["reviewing"],
            status_counts["accepted"],
            status_counts["rejected"],
        ],
    })

    # Line chart: views per job (top 8 most-viewed)
    top8_views = jobs_with_stats.order_by("-views")[:8]
    views_chart = json.dumps({
        "labels": [j.title for j in top8_views],
        "data":   [j.views for j in top8_views],
    })

    context = {
        "company": company,
        "jobs_with_stats": jobs_with_stats,
        "status_counts": status_counts,
        "top_by_views": top_by_views,
        "top_by_applications": top_by_applications,
        "totals": totals,
        "applications_chart": applications_chart,
        "status_chart": status_chart,
        "views_chart": views_chart,
    }
    return render(request, "accounts/employer_analytics.html", context)
