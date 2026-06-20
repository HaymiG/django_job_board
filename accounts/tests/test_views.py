"""
accounts/tests/test_views.py
─────────────────────────────
View tests for the accounts app: profile, dashboards, analytics.

What we test:
  • Profile page: login required, renders correctly, POST updates profile
  • Employer dashboard: login required, employer-only, correct template
  • Job seeker dashboard: login required, seeker-only, correct template
  • Employer analytics: redirects if no company, renders with company
  • Permission enforcement: wrong role → redirect to profile
"""

from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import User, UserRole
from jobs.models import Application, Company, Job


class ProfileViewTest(TestCase):
    """Tests for the /accounts/profile/ view."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="alice",
            password="TestPass!123",
            email="alice@example.com",
        )
        self.url = reverse("accounts:profile")

    def test_profile_requires_login(self):
        """Anonymous users should be redirected to the login page."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response["Location"])

    def test_profile_returns_200_when_logged_in(self):
        """Authenticated users should see the profile page."""
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/profile.html")

    def test_profile_post_updates_email(self):
        """A valid POST should update the user's email and redirect."""
        self.client.force_login(self.user)
        response = self.client.post(
            self.url,
            {
                "username": "alice",
                "email": "newemail@example.com",
                "first_name": "",
                "last_name": "",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "newemail@example.com")


class EmployerDashboardPermissionTest(TestCase):
    """Tests for role-based access to the employer dashboard."""

    def setUp(self):
        self.client = Client()
        self.employer = User.objects.create_user(
            username="emp", password="TestPass!123", role=UserRole.EMPLOYER
        )
        self.seeker = User.objects.create_user(
            username="seek", password="TestPass!123", role=UserRole.JOB_SEEKER
        )
        self.url = reverse("accounts:employer_dashboard")

    def test_anonymous_redirects_to_login(self):
        """Anonymous users should not access the employer dashboard."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_employer_can_access_dashboard(self):
        """Employers should see their dashboard (200)."""
        self.client.force_login(self.employer)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/employer_dashboard.html")

    def test_job_seeker_cannot_access_employer_dashboard(self):
        """Job seekers should be redirected away from the employer dashboard."""
        self.client.force_login(self.seeker)
        response = self.client.get(self.url)
        # role_required decorator redirects to accounts:profile
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:profile"), response["Location"])


class JobSeekerDashboardPermissionTest(TestCase):
    """Tests for role-based access to the job seeker dashboard."""

    def setUp(self):
        self.client = Client()
        self.employer = User.objects.create_user(
            username="emp2", password="TestPass!123", role=UserRole.EMPLOYER
        )
        self.seeker = User.objects.create_user(
            username="seek2", password="TestPass!123", role=UserRole.JOB_SEEKER
        )
        self.url = reverse("accounts:job_seeker_dashboard")

    def test_job_seeker_can_access_dashboard(self):
        """Job seekers should see their dashboard (200)."""
        self.client.force_login(self.seeker)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/job_seeker_dashboard.html")

    def test_employer_cannot_access_seeker_dashboard(self):
        """Employers should be redirected away from the job seeker dashboard."""
        self.client.force_login(self.employer)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_seeker_dashboard_shows_applications(self):
        """The seeker dashboard should include the user's applications in context."""
        # Create supporting objects
        employer_user = User.objects.create_user(
            username="emp_owner", password="TestPass!123", role=UserRole.EMPLOYER
        )
        company = Company.objects.create(owner=employer_user, name="Acme Ltd")
        job = Job.objects.create(
            company=company,
            title="Software Engineer",
            description="Build great things.",
        )
        Application.objects.create(job=job, applicant=self.seeker)

        self.client.force_login(self.seeker)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("applications", response.context)
        self.assertEqual(len(response.context["applications"]), 1)


class EmployerAnalyticsViewTest(TestCase):
    """Tests for the employer analytics view."""

    def setUp(self):
        self.client = Client()
        self.employer = User.objects.create_user(
            username="emp_analytics", password="TestPass!123", role=UserRole.EMPLOYER
        )
        self.url = reverse("accounts:employer_analytics")

    def test_no_company_redirects_to_dashboard(self):
        """An employer without a company profile should be redirected."""
        self.client.force_login(self.employer)
        response = self.client.get(self.url)
        self.assertRedirects(
            response,
            reverse("accounts:employer_dashboard"),
            fetch_redirect_response=False,
        )

    def test_analytics_renders_with_company(self):
        """An employer with a company should see the analytics page."""
        Company.objects.create(owner=self.employer, name="Acme Corp")
        self.client.force_login(self.employer)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/employer_analytics.html")
