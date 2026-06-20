"""
jobs/tests/test_saved_jobs.py
──────────────────────────────
Tests for the save/unsave toggle and saved jobs list.

What we test:
  toggle_save_job:
    • Only POST is accepted (GET → 403)
    • Anonymous user is redirected to login
    • First POST saves the job
    • Second POST (toggle) removes the job from saved
    • AJAX request returns JSON response

  saved_jobs view:
    • Requires login
    • Shows only active saved jobs for the current user
    • Inactive saved jobs are excluded
"""

from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import User, UserRole
from jobs.models import Company, Job


def make_seeker(username="seek_save"):
    return User.objects.create_user(
        username=username, password="TestPass!123", role=UserRole.JOB_SEEKER
    )


def make_employer(username="emp_save"):
    return User.objects.create_user(
        username=username, password="TestPass!123", role=UserRole.EMPLOYER
    )


def make_job(company, title="Save Test Job", is_active=True):
    return Job.objects.create(
        company=company,
        title=title,
        description="A job to save.",
        is_active=is_active,
    )


class ToggleSaveJobTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.seeker = make_seeker("seek_toggle")
        self.employer = make_employer("emp_toggle")
        self.company = Company.objects.create(owner=self.employer, name="ToggleCo")
        self.job = make_job(self.company)
        self.url = reverse("jobs:toggle_save_job", args=[self.job.pk])

    def test_get_request_is_forbidden(self):
        self.client.force_login(self.seeker)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_anonymous_post_redirects_to_login(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response["Location"])

    def test_first_post_saves_job(self):
        self.client.force_login(self.seeker)
        self.client.post(self.url)
        self.assertTrue(self.job.saved_by.filter(pk=self.seeker.pk).exists())

    def test_second_post_removes_saved_job(self):
        """Toggle: save → unsave."""
        self.job.saved_by.add(self.seeker)
        self.client.force_login(self.seeker)
        self.client.post(self.url)
        self.assertFalse(self.job.saved_by.filter(pk=self.seeker.pk).exists())

    def test_ajax_save_returns_json_saved_true(self):
        self.client.force_login(self.seeker)
        response = self.client.post(
            self.url,
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("saved", data)
        self.assertTrue(data["saved"])

    def test_ajax_unsave_returns_json_saved_false(self):
        self.job.saved_by.add(self.seeker)
        self.client.force_login(self.seeker)
        response = self.client.post(
            self.url,
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["saved"])


class SavedJobsListViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.seeker = make_seeker("seek_list_save")
        self.employer = make_employer("emp_list_save")
        self.company = Company.objects.create(owner=self.employer, name="ListSaveCo")
        self.active_job = make_job(self.company, title="Active Saved Job")
        self.inactive_job = make_job(
            self.company, title="Inactive Saved Job", is_active=False
        )
        self.url = reverse("jobs:saved_jobs")

    def test_requires_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_empty_saved_jobs_returns_200(self):
        self.client.force_login(self.seeker)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "jobs/saved_jobs.html")

    def test_active_saved_job_appears_in_list(self):
        self.active_job.saved_by.add(self.seeker)
        self.client.force_login(self.seeker)
        response = self.client.get(self.url)
        saved = list(response.context["saved_jobs"])
        self.assertEqual(len(saved), 1)
        self.assertEqual(saved[0], self.active_job)

    def test_inactive_saved_job_is_excluded(self):
        """Inactive jobs should NOT appear even if saved."""
        self.inactive_job.saved_by.add(self.seeker)
        self.client.force_login(self.seeker)
        response = self.client.get(self.url)
        saved = list(response.context["saved_jobs"])
        self.assertEqual(len(saved), 0)

    def test_only_current_users_saved_jobs_are_shown(self):
        """Jobs saved by another user should not appear for the current user."""
        other_seeker = make_seeker("other_seeker_s")
        self.active_job.saved_by.add(other_seeker)  # saved by someone else
        self.client.force_login(self.seeker)
        response = self.client.get(self.url)
        saved = list(response.context["saved_jobs"])
        self.assertEqual(len(saved), 0)
