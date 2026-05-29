from django.contrib.auth.models import AbstractUser
from django.db import models


class UserRole(models.TextChoices):
    EMPLOYER = "employer", "Employer"
    JOB_SEEKER = "job_seeker", "Job seeker"


class User(AbstractUser):
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.JOB_SEEKER,
    )
