from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.core.paginator import Paginator

from accounts.decorators import employer_required, job_seeker_required
from .forms import ApplicationForm, JobForm
from .models import Application, ApplicationStatus, Company, Job, JobCategory, JobType


def home(request):
    """Display homepage with recent jobs and statistics."""
    recent_jobs = Job.objects.filter(is_active=True).select_related("company")[:6]
    context = {
        "recent_jobs": recent_jobs,
        "stats": {
            "jobs": Job.objects.filter(is_active=True).count(),
            "companies": Company.objects.count(),
            "applications": Application.objects.count(),
        },
    }
    return render(request, "jobs/home.html", context)


def job_list(request):
    """Display all active job listings with filtering and search."""
    jobs = Job.objects.filter(is_active=True).select_related("company")

    # --- Keyword search (Q objects: OR across multiple fields) ---
    query = request.GET.get("q", "").strip()
    if query:
        jobs = jobs.filter(
            Q(title__icontains=query)
            | Q(description__icontains=query)
            | Q(company__name__icontains=query)
        )

    # --- Filter by job type (QuerySet chaining) ---
    job_type = request.GET.get("job_type", "")
    if job_type:
        jobs = jobs.filter(job_type=job_type)

    # --- Filter by category ---
    category = request.GET.get("category", "")
    if category:
        jobs = jobs.filter(category=category)

    # --- Filter by location ---
    location = request.GET.get("location", "").strip()
    if location:
        jobs = jobs.filter(location__icontains=location)

    # --- Pagination (Django Paginator) ---
    paginator = Paginator(jobs, 10)  # 10 jobs per page
    page = request.GET.get("page")
    jobs_page = paginator.get_page(page)

    context = {
        "jobs": jobs_page,
        "query": query,
        "job_type": job_type,
        "category": category,
        "location": location,
        "job_type_choices": JobType.choices,
        "category_choices": JobCategory.choices,
    }
    return render(request, "jobs/job_list.html", context)


def job_detail(request, pk):
    """Display full job posting details."""
    job = get_object_or_404(Job, pk=pk, is_active=True)

    # Check if user already applied
    has_applied = False
    user_application = None
    if request.user.is_authenticated:
        user_application = job.applications.filter(applicant=request.user).first()
        has_applied = user_application is not None

    # Check if current user is the job owner (employer)
    is_job_owner = (
        request.user.is_authenticated
        and job.company.owner == request.user
    )

    # Provide the application form for job seekers who haven't applied yet
    application_form = None
    if (
        request.user.is_authenticated
        and not has_applied
        and not is_job_owner
        and getattr(request.user, "role", None) == "job_seeker"
    ):
        application_form = ApplicationForm()

    context = {
        "job": job,
        "has_applied": has_applied,
        "user_application": user_application,
        "is_job_owner": is_job_owner,
        "application_form": application_form,
    }
    return render(request, "jobs/job_detail.html", context)


@job_seeker_required
def apply_to_job(request, pk):
    """Allow job seekers to apply to a job posting."""
    job = get_object_or_404(Job, pk=pk, is_active=True)

    # Check if already applied
    if job.applications.filter(applicant=request.user).exists():
        messages.info(request, "You have already applied for this job.")
        return redirect("jobs:job_detail", pk=job.pk)

    if request.method == "POST":
        form = ApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save(commit=False)
            application.job = job
            application.applicant = request.user
            application.save()
            messages.success(
                request,
                f'Your application for "{job.title}" has been submitted!'
            )
            return redirect("jobs:job_detail", pk=job.pk)
    else:
        form = ApplicationForm()

    context = {
        "form": form,
        "job": job,
    }
    return render(request, "jobs/apply_to_job.html", context)


@employer_required
def job_applicants(request, pk):
    """Allow employers to view all applicants for a specific job."""
    job = get_object_or_404(Job, pk=pk)

    # Verify this job belongs to the current user's company
    if job.company.owner != request.user:
        messages.error(request, "You can only view applicants for your own jobs.")
        return redirect("accounts:employer_dashboard")

    applications = job.applications.select_related("applicant").order_by("-created_at")

    # Filter by status
    status_filter = request.GET.get("status", "")
    if status_filter:
        applications = applications.filter(status=status_filter)

    context = {
        "job": job,
        "applications": applications,
        "status_filter": status_filter,
        "status_choices": ApplicationStatus.choices,
    }
    return render(request, "jobs/job_applicants.html", context)


@employer_required
def update_application_status(request, pk, status):
    """Allow employers to update an application's status."""
    if request.method != "POST":
        return HttpResponseForbidden("Method not allowed.")

    application = get_object_or_404(
        Application.objects.select_related("job__company"),
        pk=pk,
    )

    # Verify this application's job belongs to the current user's company
    if application.job.company.owner != request.user:
        messages.error(request, "You do not have permission to update this application.")
        return redirect("accounts:employer_dashboard")

    # Validate status value
    valid_statuses = [choice[0] for choice in ApplicationStatus.choices]
    if status not in valid_statuses:
        messages.error(request, f'Invalid status: "{status}".')
        return redirect("jobs:job_applicants", pk=application.job.pk)

    application.status = status
    application.save(update_fields=["status"])
    messages.success(
        request,
        f"Application from {application.applicant.username} marked as "
        f'"{application.get_status_display()}".'
    )
    return redirect("jobs:job_applicants", pk=application.job.pk)


@employer_required
def create_job(request):
    """Allow employers to create a new job posting."""
    # Get the company owned by this employer
    try:
        company = Company.objects.get(owner=request.user)
    except Company.DoesNotExist:
        messages.error(request, "You must create a company profile first.")
        return redirect("accounts:profile")

    if request.method == "POST":
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.company = company
            job.save()
            messages.success(request, f'Job "{job.title}" posted successfully!')
            return redirect("jobs:job_detail", pk=job.pk)
    else:
        form = JobForm()

    context = {"form": form, "title": "Post a Job", "company": company}
    return render(request, "jobs/job_form.html", context)


@employer_required
def edit_job(request, pk):
    """Allow employers to edit their own job postings."""
    job = get_object_or_404(Job, pk=pk)
    
    # Verify this job belongs to the current user's company
    if job.company.owner != request.user:
        messages.error(request, "You can only edit your own jobs.")
        return redirect("jobs:job_list")

    if request.method == "POST":
        form = JobForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            messages.success(request, "Job updated successfully!")
            return redirect("jobs:job_detail", pk=job.pk)
    else:
        form = JobForm(instance=job)

    context = {"form": form, "job": job, "title": f"Edit: {job.title}"}
    return render(request, "jobs/job_form.html", context)


@employer_required
def delete_job(request, pk):
    """Allow employers to delete their own job postings."""
    job = get_object_or_404(Job, pk=pk)
    
    # Verify this job belongs to the current user's company
    if job.company.owner != request.user:
        messages.error(request, "You can only delete your own jobs.")
        return redirect("jobs:job_list")

    if request.method == "POST":
        job_title = job.title
        job.delete()
        messages.success(request, f'Job "{job_title}" deleted successfully!')
        return redirect("jobs:job_list")

    context = {"job": job}
    return render(request, "jobs/job_confirm_delete.html", context)
