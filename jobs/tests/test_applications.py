"""
jobs/tests/test_applications.py
─────────────────────────────────
Application flow tests: apply, view applicants, update status.

What we test:
  apply_to_job:
    • Anonymous user is redirected to login
    • Employer cannot apply (wrong role)
    • Job seeker can submit an application (POST)
    • Duplicate application is rejected (redirect + message)

  job_applicants:
    • Anonymous user is redirected
    • Job seeker cannot view applicants
    • Employer can view applicants for their own job
    • Employer cannot view applicants for another employer's job

  update_application_status:
    • Only POST is allowed
    • Owner employer can update the status
    • Non-owner employer is rejected
    • Invalid status value returns an error
"""

from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import User, UserRole
from jobs.models import Application, ApplicationStatus, Company, Job


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_employer(username):
    return User.objects.create_user(
        username=username, password="TestPass!123", role=UserRole.EMPLOYER
    )


def make_seeker(username):
    return User.objects.create_user(
        username=username, password="TestPass!123", role=UserRole.JOB_SEEKER
    )


def make_company(owner, name="ApplyCo"):
    return Company.objects.create(owner=owner, name=name)


def make_job(company, title="Apply Job"):
    return Job.objects.create(
        company=company, title=title, description="Apply here.", is_active=True
    )


# ── Tests ─────────────────────────────────────────────────────────────────────

class ApplyToJobViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.employer = make_employer("emp_apply")
        self.company = make_company(self.employer)
        self.job = make_job(self.company)
        self.seeker = make_seeker("seek_apply")
        self.url = reverse("jobs:apply_to_job", args=[self.job.pk])

    def test_anonymous_redirects_to_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response["Location"])

    def test_employer_cannot_apply(self):
        """Employers have the wrong role; they should be redirected."""
        self.client.force_login(self.employer)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_seeker_can_view_apply_form(self):
        self.client.force_login(self.seeker)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "jobs/apply_to_job.html")

    def test_seeker_can_submit_application(self):
        self.client.force_login(self.seeker)
        data = {"cover_letter": "I am very excited about this opportunity!"}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Application.objects.filter(job=self.job, applicant=self.seeker).exists()
        )

    def test_duplicate_application_is_rejected(self):
        """Applying twice should not create a second application."""
        Application.objects.create(job=self.job, applicant=self.seeker)
        self.client.force_login(self.seeker)
        data = {"cover_letter": "Another try!"}
        response = self.client.post(self.url, data)
        # Should redirect with info message, not create a duplicate
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            Application.objects.filter(job=self.job, applicant=self.seeker).count(), 1
        )


class JobApplicantsViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.employer = make_employer("emp_applicants")
        self.company = make_company(self.employer)
        self.job = make_job(self.company)
        self.seeker = make_seeker("seek_applicants")
        Application.objects.create(job=self.job, applicant=self.seeker)
        self.url = reverse("jobs:job_applicants", args=[self.job.pk])

        # A different employer who does NOT own this job
        self.other_employer = make_employer("emp_other_app")
        make_company(self.other_employer, "OtherCo2")

    def test_anonymous_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_seeker_cannot_view_applicants(self):
        self.client.force_login(self.seeker)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_owner_employer_can_view_applicants(self):
        self.client.force_login(self.employer)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "jobs/job_applicants.html")
        self.assertIn("applications", response.context)
        self.assertEqual(len(response.context["applications"]), 1)

    def test_non_owner_employer_is_redirected(self):
        self.client.force_login(self.other_employer)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)


class UpdateApplicationStatusViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.employer = make_employer("emp_status")
        self.company = make_company(self.employer)
        self.job = make_job(self.company)
        self.seeker = make_seeker("seek_status")
        self.application = Application.objects.create(
            job=self.job, applicant=self.seeker
        )
        self.url = reverse(
            "jobs:update_application_status",
            args=[self.application.pk, ApplicationStatus.REVIEWING],
        )

    def test_get_request_is_forbidden(self):
        self.client.force_login(self.employer)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_owner_employer_can_update_status(self):
        self.client.force_login(self.employer)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, ApplicationStatus.REVIEWING)

    def test_invalid_status_value_does_not_update(self):
        self.client.force_login(self.employer)
        bad_url = reverse(
            "jobs:update_application_status",
            args=[self.application.pk, "invalid_status"],
        )
        response = self.client.post(bad_url)
        # Should redirect with an error message
        self.assertEqual(response.status_code, 302)
        self.application.refresh_from_db()
        # Status should remain unchanged
        self.assertEqual(self.application.status, ApplicationStatus.SUBMITTED)

    def test_non_owner_employer_cannot_update_status(self):
        other_employer = make_employer("emp_not_owner")
        make_company(other_employer, "OtherCo3")
        self.client.force_login(other_employer)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.application.refresh_from_db()
        # Status should NOT have changed
        self.assertEqual(self.application.status, ApplicationStatus.SUBMITTED)
