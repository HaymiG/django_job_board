from django.contrib import admin

from .models import Application, Company, Job


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "website", "created_at")
    search_fields = ("name", "owner__username", "owner__email")


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("title", "company", "location", "is_active", "created_at")
    list_filter = ("is_active", "company")
    search_fields = ("title", "company__name", "location")


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("job", "applicant", "status", "created_at")
    list_filter = ("status", "job__company")
    search_fields = ("job__title", "applicant__username", "applicant__email")
