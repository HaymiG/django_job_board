from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.register, name="register"),
    path("login/", views.UserLoginView.as_view(), name="login"),
    path("logout/", views.UserLogoutView.as_view(), name="logout"),
    path("profile/", views.profile, name="profile"),
    path("dashboard/employer/", views.employer_dashboard, name="employer_dashboard"),
    path("dashboard/employer/analytics/", views.employer_analytics, name="employer_analytics"),
    path("dashboard/seeker/", views.job_seeker_dashboard, name="job_seeker_dashboard"),
]
