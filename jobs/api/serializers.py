"""
jobs/api/serializers.py

What is a Serializer?
─────────────────────
A serializer converts between complex Python objects (Django model instances,
QuerySets) and primitive data types (dicts, lists) that can then be rendered
into JSON or XML for an HTTP response.

ORM object ──(serialize)──▶ Python dict ──▶ JSON  (outbound)
JSON        ──(parse)──────▶ Python dict ──▶ save() (inbound)

ModelSerializer is a shortcut that auto-generates fields from the model's
field definitions — you only need to declare Meta.model and Meta.fields.
"""

from rest_framework import serializers

from ..models import Application, Company, Job


class CompanyBriefSerializer(serializers.ModelSerializer):
    """Compact company representation — used nested inside JobSerializer."""

    class Meta:
        model = Company
        fields = ["id", "name", "website"]


class JobSerializer(serializers.ModelSerializer):
    """
    Full job listing representation.

    SerializerMethodField lets us add computed / read-only properties that
    don't map 1-to-1 to a model field.
    """

    # Nested object — embeds company data instead of just a raw FK id
    company = CompanyBriefSerializer(read_only=True)

    # Human-readable label for the choice fields (e.g. "Full-time" not "full_time")
    job_type_display = serializers.CharField(
        source="get_job_type_display", read_only=True
    )
    category_display = serializers.CharField(
        source="get_category_display", read_only=True
    )

    # Computed field — total number of applications for this job
    application_count = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = [
            "id",
            "title",
            "company",
            "location",
            "job_type",
            "job_type_display",
            "category",
            "category_display",
            "salary_min",
            "salary_max",
            "salary_currency",
            "description",
            "views",
            "application_count",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["views", "created_at", "updated_at"]

    def get_application_count(self, obj):
        """Return the number of applications for this job."""
        return obj.applications.count()


class ApplicationSerializer(serializers.ModelSerializer):
    """
    Application serializer — used by job seekers to view their own applications.

    The `applicant` field is set automatically from request.user in the view,
    so it is read-only here. We expose job title/company via nested fields
    so the client doesn't need to make extra API calls.
    """

    # Read-only computed fields from related objects
    job_title = serializers.CharField(source="job.title", read_only=True)
    company_name = serializers.CharField(source="job.company.name", read_only=True)
    applicant_username = serializers.CharField(
        source="applicant.username", read_only=True
    )
    status_display = serializers.CharField(
        source="get_status_display", read_only=True
    )

    class Meta:
        model = Application
        fields = [
            "id",
            "job",
            "job_title",
            "company_name",
            "applicant_username",
            "cover_letter",
            "resume",
            "status",
            "status_display",
            "created_at",
        ]
        read_only_fields = ["status", "created_at", "applicant_username"]
