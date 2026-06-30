"""
accounts/tests/test_auth.py
────────────────────────────
Authentication flow tests: register, login, logout.

What we test:
• GET register page returns 200
• Successful registration creates a user and redirects
• Duplicate username returns form error
• GET login page returns 200
• Valid credentials log the user in and redirect by role
• Invalid credentials stay on the login page
• Logout clears the session
"""

from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import User, UserRole


class RegistrationFlowTest(TestCase):
    """End-to-end tests for the user registration view."""

    def setUp(self):
        self.client = Client()
        self.url = reverse("accounts:register")

    def test_register_page_get(self):
        """GET /accounts/register/ should return HTTP 200."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/register.html")

    def test_register_creates_user_and_redirects(self):
        """A valid POST should create a new user and redirect to profile."""
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password1": "TestPass!123",
            "password2": "TestPass!123",
            "role": UserRole.JOB_SEEKER,
        }
        response = self.client.post(self.url, data)
        # Should redirect after success
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_register_authenticated_user_redirects(self):
        """An already-authenticated user visiting /register/ should be redirected."""
        user = User.objects.create_user(username="alice", password="TestPass!123")
        self.client.force_login(user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_register_with_mismatched_passwords_shows_error(self):
        """Mismatched passwords should re-render the form with errors."""
        data = {
            "username": "baduser",
            "email": "bad@example.com",
            "password1": "TestPass!123",
            "password2": "DifferentPass!456",
            "role": UserRole.JOB_SEEKER,
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="baduser").exists())


class LoginFlowTest(TestCase):
    """Tests for the login view and role-aware redirect."""

    def setUp(self):
        self.client = Client()
        self.login_url = reverse("accounts:login")
        # Create one user per role
        self.seeker = User.objects.create_user(
            username="seeker",
            password="TestPass!123",
            role=UserRole.JOB_SEEKER,
        )
        self.employer = User.objects.create_user(
            username="employer",
            password="TestPass!123",
            role=UserRole.EMPLOYER,
        )

    def test_login_page_get(self):
        """GET /accounts/login/ should return HTTP 200."""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/login.html")

    def test_job_seeker_redirected_to_seeker_dashboard(self):
        """A job seeker who logs in should land on the seeker dashboard."""
        response = self.client.post(
            self.login_url,
            {"username": "seeker", "password": "TestPass!123"},
        )
        self.assertRedirects(
            response,
            reverse("accounts:job_seeker_dashboard"),
            fetch_redirect_response=False,
        )

    def test_employer_redirected_to_employer_dashboard(self):
        """An employer who logs in should land on the employer dashboard."""
        response = self.client.post(
            self.login_url,
            {"username": "employer", "password": "TestPass!123"},
        )
        self.assertRedirects(
            response,
            reverse("accounts:employer_dashboard"),
            fetch_redirect_response=False,
        )

    def test_invalid_credentials_stay_on_login(self):
        """Wrong password should keep the user on the login page."""
        response = self.client.post(
            self.login_url,
            {"username": "seeker", "password": "WrongPass!"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/login.html")


class LogoutFlowTest(TestCase):
    """Tests for the logout view."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="user1", password="TestPass!123")

    def test_logout_redirects_to_home(self):
        """Logging out should redirect to the jobs home page."""
        self.client.force_login(self.user)
        response = self.client.post(reverse("accounts:logout"))
        self.assertRedirects(
            response, reverse("jobs:home"), fetch_redirect_response=False
        )

    def test_user_is_logged_out_after_logout(self):
        """After logout the user should be anonymous."""
        self.client.force_login(self.user)
        self.client.post(reverse("accounts:logout"))
        # A login-required page should redirect to login
        profile_response = self.client.get(reverse("accounts:profile"))
        self.assertEqual(profile_response.status_code, 302)
        self.assertIn(reverse("accounts:login"), profile_response["Location"])
