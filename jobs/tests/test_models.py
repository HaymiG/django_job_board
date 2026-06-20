"""
jobs/tests/test_models.py
──────────────────────────
Model-level tests for Company, Job, and Application.

What we test:
  Company:
    • __str__ returns company name
    • OneToOne constraint with User

  Job:
    • __str__ returns "Title @ Company"
    • Default values (is_active, salary_currency, job_type)
    • Job ordering is newest-first
    • View counter starts at 0
    • saved_by ManyToMany works correctly

  Application:
    • __str__ format
    • Unique constraint: one application per (job, applicant)
    • Default status is 'submitted'
"""

from django.db import IntegrityError
from django.test import TestCase

from accounts.models import User, UserRole
from jobs.models import (
    Application,
    ApplicationStatus,
    Company,
    Currency,
    Job,
    JobType,
)


def make_employer(username="emp_model"):
    """Helper: create an employer user."""
    return User.objects.create_user(
        username=username, password="TestPass!123", role=UserRole.EMPLOYER
    )


def make_seeker(username="seek_model"):
    """Helper: create a job seeker user."""
    return User.objects.create_user(
        username=username, password="TestPass!123", role=UserRole.JOB_SEEKER
    )


def make_company(owner, name="Test Co"):
    """Helper: create a company."""
    return Company.objects.create(owner=owner, name=name)


def make_job(company, title="Dev"):
    """Helper: create a job."""
    return Job.objects.create(
        company=company, title=title, description="Great job opportunity."
    )


class CompanyModelTest(TestCase):
    """Tests for the Company model."""

    def test_str_returns_company_name(self):
        employer = make_employer()
        company = make_company(employer, "Innovatech")
        self.assertEqual(str(company), "Innovatech")

    def test_company_has_one_to_one_with_user(self):
        """Each employer can only have one company (OneToOneField)."""
        employer = make_employer("emp_oto")
        make_company(employer, "First Inc")
        with self.assertRaises(IntegrityError):
            make_company(employer, "Second Inc")  # should fail


class JobModelTest(TestCase):
    """Tests for the Job model."""

    def setUp(self):
        self.employer = make_employer("emp_job")
        self.company = make_company(self.employer)

    def test_str_returns_title_at_company(self):
        job = make_job(self.company, title="Backend Engineer")
        self.assertEqual(str(job), "Backend Engineer @ Test Co")

    def test_default_is_active_true(self):
        job = make_job(self.company)
        self.assertTrue(job.is_active)

    def test_default_salary_currency_is_birr(self):
        job = make_job(self.company)
        self.assertEqual(job.salary_currency, Currency.BIRR)

    def test_default_job_type_is_full_time(self):
        job = make_job(self.company)
        self.assertEqual(job.job_type, JobType.FULL_TIME)

    def test_view_counter_starts_at_zero(self):
        job = make_job(self.company)
        self.assertEqual(job.views, 0)

    def test_job_ordering_is_newest_first(self):
        """The Meta ordering ensures newest jobs appear first."""
        job1 = make_job(self.company, title="Job A")
        job2 = make_job(self.company, title="Job B")
        jobs = list(Job.objects.all())
        # Job B was created after Job A, so it comes first
        self.assertEqual(jobs[0], job2)
        self.assertEqual(jobs[1], job1)

    def test_saved_by_many_to_many(self):
        """A job can be saved by multiple users."""
        seeker1 = make_seeker("seek1_m")
        seeker2 = make_seeker("seek2_m")
        job = make_job(self.company)
        job.saved_by.add(seeker1)
        job.saved_by.add(seeker2)
        self.assertEqual(job.saved_by.count(), 2)
        self.assertIn(seeker1, job.saved_by.all())

    def test_remove_from_saved_by(self):
        """Removing a user from saved_by should work correctly."""
        seeker = make_seeker("seek_rem")
        job = make_job(self.company)
        job.saved_by.add(seeker)
        job.saved_by.remove(seeker)
        self.assertFalse(job.saved_by.filter(pk=seeker.pk).exists())


class ApplicationModelTest(TestCase):
    """Tests for the Application model."""

    def setUp(self):
        self.employer = make_employer("emp_app")
        self.company = make_company(self.employer)
        self.job = make_job(self.company)
        self.seeker = make_seeker("seek_app")

    def test_str_format(self):
        app = Application.objects.create(job=self.job, applicant=self.seeker)
        self.assertEqual(str(app), f"{self.seeker.username} -> {self.job.title}")

    def test_default_status_is_submitted(self):
        app = Application.objects.create(job=self.job, applicant=self.seeker)
        self.assertEqual(app.status, ApplicationStatus.SUBMITTED)

    def test_unique_constraint_prevents_duplicate_application(self):
        """A user cannot apply to the same job twice."""
        Application.objects.create(job=self.job, applicant=self.seeker)
        with self.assertRaises(IntegrityError):
            Application.objects.create(job=self.job, applicant=self.seeker)

    def test_application_belongs_to_correct_job_and_user(self):
        app = Application.objects.create(job=self.job, applicant=self.seeker)
        self.assertEqual(app.job, self.job)
        self.assertEqual(app.applicant, self.seeker)
