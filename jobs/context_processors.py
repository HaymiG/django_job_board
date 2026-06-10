def saved_jobs_count(request):
    """
    Injects `saved_jobs_count` into every template context.

    Context processors run on every request, making this the cleanest way to
    show a live badge in the navbar without modifying every single view.

    Only queries the DB when a job-seeker is logged in — zero cost for guests
    and employers.
    """
    count = 0
    if (
        request.user.is_authenticated
        and getattr(request.user, "role", None) == "job_seeker"
    ):
        count = request.user.saved_jobs.filter(is_active=True).count()
    return {"saved_jobs_count": count}
