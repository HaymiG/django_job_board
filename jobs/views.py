from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.core.paginator import Paginator

from accounts.decorators import employer_required
from .forms import JobForm
from .models import Application, Company, Job, JobType


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

    # Search by title or location
    query = request.GET.get("q", "")
    if query:
        jobs = jobs.filter(Q(title__icontains=query) | Q(location__icontains=query))

    # Filter by job type
    job_type = request.GET.get("job_type", "")
    if job_type:
        jobs = jobs.filter(job_type=job_type)

    # Pagination
    paginator = Paginator(jobs, 10)  # 10 jobs per page
    page = request.GET.get("page")
    jobs_page = paginator.get_page(page)

    context = {
        "jobs": jobs_page,
        "query": query,
        "job_type": job_type,
        "job_type_choices": JobType.choices,
    }
    return render(request, "jobs/job_list.html", context)


def job_detail(request, pk):
    """Display full job posting details."""
    job = get_object_or_404(Job, pk=pk, is_active=True)

    # Check if user already applied
    has_applied = False
    if request.user.is_authenticated:
        has_applied = job.applications.filter(applicant=request.user).exists()

    # Check if current user is the job owner (employer)
    is_job_owner = (
        request.user.is_authenticated
        and job.company.owner == request.user
    )

    context = {
        "job": job,
        "has_applied": has_applied,
        "is_job_owner": is_job_owner,
    }
    return render(request, "jobs/job_detail.html", context)


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
