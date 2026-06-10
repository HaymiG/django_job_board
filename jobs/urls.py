from django.urls import path

from . import views

app_name = "jobs"

urlpatterns = [
    path("", views.home, name="home"),
    path("browse/", views.job_list, name="job_list"),
    path("saved/", views.saved_jobs, name="saved_jobs"),
    path("job/<int:pk>/", views.job_detail, name="job_detail"),
    path("job/create/", views.create_job, name="create_job"),
    path("job/<int:pk>/edit/", views.edit_job, name="edit_job"),
    path("job/<int:pk>/delete/", views.delete_job, name="delete_job"),
    path("job/<int:pk>/apply/", views.apply_to_job, name="apply_to_job"),
    path("job/<int:pk>/save/", views.toggle_save_job, name="toggle_save_job"),
    path("job/<int:pk>/applicants/", views.job_applicants, name="job_applicants"),
    path(
        "application/<int:pk>/status/<str:status>/",
        views.update_application_status,
        name="update_application_status",
    ),
]
