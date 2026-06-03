from django.urls import path

from . import views

app_name = "jobs"

urlpatterns = [
    path("", views.home, name="home"),
    path("browse/", views.job_list, name="job_list"),
    path("job/<int:pk>/", views.job_detail, name="job_detail"),
    path("job/create/", views.create_job, name="create_job"),
    path("job/<int:pk>/edit/", views.edit_job, name="edit_job"),
    path("job/<int:pk>/delete/", views.delete_job, name="delete_job"),
]
