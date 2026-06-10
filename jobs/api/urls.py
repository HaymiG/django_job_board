"""
jobs/api/urls.py

DRF Router — auto-generates URL patterns from ViewSets.

A DefaultRouter wired to two ViewSets produces these URLs automatically:

  GET/POST   /api/jobs/                   → JobViewSet.list / create
  GET        /api/jobs/{id}/              → JobViewSet.retrieve
  POST       /api/jobs/{id}/save/         → JobViewSet.toggle_save (@action)
  GET/POST   /api/applications/           → ApplicationViewSet.list / create
  GET/DELETE /api/applications/{id}/      → ApplicationViewSet.retrieve / destroy

  GET        /api/                        → API root (browsable API index)
  POST       /api/auth/token/             → obtain auth token
  GET        /api/schema/                 → OpenAPI schema (if installed)
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token

from .views import ApplicationViewSet, JobViewSet

# Router — maps ViewSet to URL patterns automatically
# compare: manually writing path("jobs/", list_view), path("jobs/<pk>/", detail_view)
router = DefaultRouter()
router.register(r"jobs", JobViewSet, basename="job")
router.register(r"applications", ApplicationViewSet, basename="application")

urlpatterns = [
    path("", include(router.urls)),
    # Token endpoint: POST {"username": "...", "password": "..."}
    # Returns:        {"token": "9944b09199c62bcf..."}
    path("auth/token/", obtain_auth_token, name="api_token_auth"),
]
