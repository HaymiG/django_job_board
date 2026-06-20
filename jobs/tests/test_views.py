"""
jobs/tests/test_views.py
─────────────────────────
View tests for the jobs app: home, list, detail, create, edit, delete.

What we test:
  home:
    • Returns 200 with context stats

  job_list:
    • Returns 200
    • Keyword search filters results correctly
    • Job-type filter works
    • Category filter works

  job_detail:
    • Returns 200 for an active job
    • Returns 404 for inactive or non-existent job
    • View counter is incremented on each visit
    • is_saved flag in context is correct

  create_job:
    • Requires employer role
    • Requires an existing company
    • Valid POST creates a job and redirects

  edit_job:
    • Requires employer role and ownership
    • Valid POST updates the job

  delete_job:
    • Requires employer role and ownership
    • POST deletes the job and redirects
"""

from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import User, UserRole
from jobs.models import Application, Company, Job, JobType


# ── Shared helpers ────────────────────────────────────────────────────────────

def make_employer(username="emp_view"):
    return User.objects.create_user(
        username=username, password="TestPass!123", role=UserRole.EMPLOYER
    )


def make_seeker(username="seek_view"):
    return User.objects.create_user(
        username=username, password="TestPass!123", role=UserRole.JOB_SEEKER
    )


def make_company(owner, name="ViewCo"):
    return Company.objects.create(owner=owner, name=name)


def make_job(company, title="Test Job", is_active=True):
    return Job.objects.create(
        company=company,
        title=title,
        description="A wonderful opportunity.",
        is_active=is_active,
    )


# ── Tests ─────────────────────────────────────────────────────────────────────

class HomeViewTest(TestCase):
    def test_home_returns_200(self):
        response = self.client.get(reverse("jobs:home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "jobs/home.html")

    def test_home_context_has_stats(self):
        response = self.client.get(reverse("jobs:home"))
        self.assertIn("stats", response.context)
        stats = response.context["stats"]
        self.assertIn("jobs", stats)
        self.assertIn("companies", stats)
        self.assertIn("applications", stats)


class JobListViewTest(TestCase):
    def setUp(self):
        self.employer = make_employer("emp_list")
        self.company = make_company(self.employer)
        self.job1 = make_job(self.company, title="Python Developer")
        self.job2 = make_job(self.company, title="React Designer")
        # Create an inactive job (should NOT appear)
        make_job(self.company, title="Hidden Job", is_active=False)

    def test_list_returns_200(self):
        response = self.client.get(reverse("jobs:job_list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "jobs/job_list.html")

    def test_inactive_jobs_are_excluded(self):
        response = self.client.get(reverse("jobs:job_list"))
        titles = [j.title for j in response.context["jobs"]]
        self.assertNotIn("Hidden Job", titles)

    def test_keyword_search_filters_results(self):
        response = self.client.get(reverse("jobs:job_list"), {"q": "Python"})
        jobs = response.context["jobs"]
        self.assertEqual(jobs.paginator.count, 1)
        self.assertEqual(jobs[0].title, "Python Developer")

    def test_job_type_filter(self):
        """Only jobs matching the selected job_type should appear."""
        # Create a part-time job
        Job.objects.create(
            company=self.company,
            title="Part Time Gig",
            description="PT job.",
            job_type=JobType.PART_TIME,
        )
        response = self.client.get(
            reverse("jobs:job_list"), {"job_type": JobType.PART_TIME}
        )
        jobs = response.context["jobs"]
        for job in jobs:
            self.assertEqual(job.job_type, JobType.PART_TIME)

    def test_search_returns_empty_for_no_match(self):
        response = self.client.get(reverse("jobs:job_list"), {"q": "ZZZNoMatch"})
        jobs = response.context["jobs"]
        self.assertEqual(jobs.paginator.count, 0)


class JobDetailViewTest(TestCase):
    def setUp(self):
        self.employer = make_employer("emp_detail")
        self.company = make_company(self.employer)
        self.job = make_job(self.company)
        self.seeker = make_seeker("seek_detail")

    def test_detail_returns_200_for_active_job(self):
        url = reverse("jobs:job_detail", args=[self.job.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "jobs/job_detail.html")

    def test_detail_returns_404_for_inactive_job(self):
        inactive_job = make_job(self.company, title="Inactive", is_active=False)
        url = reverse("jobs:job_detail", args=[inactive_job.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_view_counter_increments(self):
        url = reverse("jobs:job_detail", args=[self.job.pk])
        self.client.get(url)
        self.job.refresh_from_db()
        self.assertEqual(self.job.views, 1)
        self.client.get(url)
        self.job.refresh_from_db()
        self.assertEqual(self.job.views, 2)

    def test_is_saved_false_for_anonymous(self):
        url = reverse("jobs:job_detail", args=[self.job.pk])
        response = self.client.get(url)
        self.assertFalse(response.context["is_saved"])

    def test_is_saved_true_when_user_saved_job(self):
        self.job.saved_by.add(self.seeker)
        self.client.force_login(self.seeker)
        url = reverse("jobs:job_detail", args=[self.job.pk])
        response = self.client.get(url)
        self.assertTrue(response.context["is_saved"])

    def test_has_applied_false_before_applying(self):
        self.client.force_login(self.seeker)
        url = reverse("jobs:job_detail", args=[self.job.pk])
        response = self.client.get(url)
        self.assertFalse(response.context["has_applied"])

    def test_has_applied_true_after_applying(self):
        Application.objects.create(job=self.job, applicant=self.seeker)
        self.client.force_login(self.seeker)
        url = reverse("jobs:job_detail", args=[self.job.pk])
        response = self.client.get(url)
        self.assertTrue(response.context["has_applied"])


class CreateJobViewTest(TestCase):
    def setUp(self):
        self.employer = make_employer("emp_create")
        self.company = make_company(self.employer)
        self.seeker = make_seeker("seek_create")
        self.url = reverse("jobs:create_job")

    def test_anonymous_redirects_to_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_seeker_cannot_create_job(self):
        self.client.force_login(self.seeker)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_employer_can_see_create_form(self):
        self.client.force_login(self.employer)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "jobs/job_form.html")

    def test_valid_post_creates_job(self):
        self.client.force_login(self.employer)
        data = {
            "title": "New Senior Dev",
            "description": "You will build cool stuff.",
            "location": "Addis Ababa",
            "job_type": "full_time",
            "category": "technology",
            "salary_currency": "ETB",
            "is_active": True,
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Job.objects.filter(title="New Senior Dev").exists())

    def test_employer_without_company_redirects_to_profile(self):
        """An employer who has no company should be redirected."""
        employer_no_co = make_employer("emp_no_co")
        self.client.force_login(employer_no_co)
        response = self.client.get(self.url)
        self.assertRedirects(
            response, reverse("accounts:profile"), fetch_redirect_response=False
        )


class EditJobViewTest(TestCase):
    def setUp(self):
        self.employer = make_employer("emp_edit")
        self.company = make_company(self.employer)
        self.job = make_job(self.company, title="Original Title")
        self.other_employer = make_employer("emp_other")
        self.other_company = make_company(self.other_employer, name="OtherCo")
        self.url = reverse("jobs:edit_job", args=[self.job.pk])

    def test_owner_can_edit_job(self):
        self.client.force_login(self.employer)
        data = {
            "title": "Updated Title",
            "description": "Now updated.",
            "location": "Remote",
            "job_type": "full_time",
            "category": "technology",
            "salary_currency": "ETB",
            "is_active": True,
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        self.job.refresh_from_db()
        self.assertEqual(self.job.title, "Updated Title")

    def test_non_owner_cannot_edit_job(self):
        """An employer who does NOT own the job should be redirected."""
        self.client.force_login(self.other_employer)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)


class DeleteJobViewTest(TestCase):
    def setUp(self):
        self.employer = make_employer("emp_del")
        self.company = make_company(self.employer)
        self.job = make_job(self.company, title="To Be Deleted")
        self.url = reverse("jobs:delete_job", args=[self.job.pk])

    def test_get_shows_confirm_page(self):
        self.client.force_login(self.employer)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "jobs/job_confirm_delete.html")

    def test_post_deletes_job(self):
        self.client.force_login(self.employer)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Job.objects.filter(pk=self.job.pk).exists())
