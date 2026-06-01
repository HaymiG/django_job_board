from django.shortcuts import render

from .models import Application, Company, Job


def home(request):
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
