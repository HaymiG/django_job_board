"""
accounts/tests/test_models.py
─────────────────────────────
Model-level tests for the User model.

What we test:
  • Default role is job_seeker
  • Role can be set to employer
  • __str__ returns the username (inherited from AbstractUser)
  • UserRole choices are correct
"""

from django.test import TestCase

from accounts.models import User, UserRole


class UserModelTest(TestCase):
    """Tests for the custom User model."""

    def test_default_role_is_job_seeker(self):
        """A freshly created user should default to the job_seeker role."""
        user = User.objects.create_user(
            username="seeker1", password="pass1234!", email="seeker1@example.com"
        )
        self.assertEqual(user.role, UserRole.JOB_SEEKER)

    def test_employer_role_can_be_set(self):
        """We should be able to explicitly set the employer role."""
        user = User.objects.create_user(
            username="employer1",
            password="pass1234!",
            email="employer1@example.com",
            role=UserRole.EMPLOYER,
        )
        self.assertEqual(user.role, UserRole.EMPLOYER)

    def test_str_returns_username(self):
        """__str__ is inherited from AbstractUser and returns the username."""
        user = User.objects.create_user(username="alice", password="pass1234!")
        self.assertEqual(str(user), "alice")

    def test_user_role_choices(self):
        """UserRole TextChoices should contain employer and job_seeker values."""
        values = [choice[0] for choice in UserRole.choices]
        self.assertIn("employer", values)
        self.assertIn("job_seeker", values)

    def test_is_active_default_true(self):
        """New users should be active by default."""
        user = User.objects.create_user(username="bob", password="pass1234!")
        self.assertTrue(user.is_active)
