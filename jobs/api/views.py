"""
jobs/api/views.py

What is a ViewSet?
──────────────────
A ViewSet is a class that groups related API actions together.
DRF maps HTTP methods to actions automatically:

HTTP Method   | Action        | URL
─────────────────────────────────────────────────────────
GET  /jobs/   | list()        | returns paginated list
POST /jobs/   | create()      | creates a new object
GET  /jobs/1/ | retrieve()    | returns single object
PUT  /jobs/1/ | update()      | full update
PATCH /jobs/1/| partial_update| partial update
DELETE /jobs/1/| destroy()    | delete

ReadOnlyModelViewSet gives only list + retrieve — perfect for public endpoints
like the jobs list that shouldn't be editable via the API.
"""

from django.db.models import F
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from ..models import Application, Job
from .serializers import ApplicationSerializer, JobSerializer


class JobViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public read-only API endpoint for job listings.

    list:   GET /api/jobs/           → paginated list of active jobs
    detail: GET /api/jobs/{id}/      → single job with full description
    save:   POST /api/jobs/{id}/save/ → toggle save for authenticated user

    Search:   ?search=python
    Order:    ?ordering=-created_at  (prefix '-' for descending)
    Filter:   ?job_type=full_time&category=technology
    """

    serializer_class = JobSerializer
    # search_fields tells SearchFilter which model fields to search
    search_fields = ["title", "description", "company__name", "location"]
    # ordering_fields controls which fields clients can sort by
    ordering_fields = ["created_at", "salary_min", "views"]
    ordering = ["-created_at"]  # default sort

    def get_queryset(self):
        """
        Returns only active jobs with company pre-fetched.
        select_related("company") issues a single SQL JOIN instead of N+1 queries.
        """
        qs = (
            Job.objects.filter(is_active=True)
            .select_related("company")
            .prefetch_related("applications")
        )

        # Manual query-param filters (DRF SearchFilter only handles search, not exact match)
        job_type = self.request.query_params.get("job_type")
        category = self.request.query_params.get("category")
        location = self.request.query_params.get("location")

        if job_type:
            qs = qs.filter(job_type=job_type)
        if category:
            qs = qs.filter(category=category)
        if location:
            qs = qs.filter(location__icontains=location)

        return qs

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve a single job AND atomically increment its view counter.

        F() is a database-level expression — the increment happens in a single
        SQL UPDATE, avoiding race conditions when two requests arrive at once.
        """
        instance = self.get_object()
        # Atomic: UPDATE jobs_job SET views = views + 1 WHERE id = <id>
        Job.objects.filter(pk=instance.pk).update(views=F("views") + 1)
        instance.refresh_from_db(fields=["views"])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[permissions.IsAuthenticated],
        url_path="save",
    )
    def toggle_save(self, request, pk=None):
        """
        POST /api/jobs/{id}/save/
        Toggle bookmarking a job for the authenticated user.
        Returns JSON {"saved": true/false}.
        """
        job = self.get_object()
        if job.saved_by.filter(pk=request.user.pk).exists():
            job.saved_by.remove(request.user)
            saved = False
        else:
            job.saved_by.add(request.user)
            saved = True
        return Response({"saved": saved}, status=status.HTTP_200_OK)


class ApplicationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for a job seeker's own applications.

    Authenticated users can only see and manage THEIR OWN applications.
    Employers cannot access this endpoint.

    list:     GET  /api/applications/       → my applications
    create:   POST /api/applications/       → submit new application
    retrieve: GET  /api/applications/{id}/  → single application
    destroy:  DELETE /api/applications/{id}/→ withdraw application
    """

    serializer_class = ApplicationSerializer
    # Both authentication classes are in settings — here we just require login
    permission_classes = [permissions.IsAuthenticated]
    # Prevent accidental updates/deletes of others' applications
    http_method_names = ["get", "post", "delete", "head", "options"]

    def get_queryset(self):
        """
        User-specific data: filter strictly to the current user.
        A job seeker can never see another user's applications through this API.
        """
        return (
            Application.objects.filter(applicant=self.request.user)
            .select_related("job", "job__company", "applicant")
            .order_by("-created_at")
        )

    def perform_create(self, serializer):
        """
        Override perform_create so we can inject applicant=request.user
        before saving — the client never sends the applicant field.
        """
        serializer.save(applicant=self.request.user)
