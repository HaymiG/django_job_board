from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from jobs.models import Application, Company, Job


class Command(BaseCommand):
    help = "Seed the database with sample employers, companies, jobs, and applications."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Delete existing seeded objects first.")

    def handle(self, *args, **options):
        User = get_user_model()

        if options["reset"]:
            Application.objects.all().delete()
            Job.objects.all().delete()
            Company.objects.all().delete()
            User.objects.filter(username__in=["employer1", "seeker1", "seeker2"]).delete()

        employer, _ = User.objects.get_or_create(
            username="employer1",
            defaults={
                "email": "employer1@example.com",
                "role": "employer",
            },
        )
        employer.set_password("password123")
        employer.save()

        seeker1, _ = User.objects.get_or_create(
            username="seeker1",
            defaults={
                "email": "seeker1@example.com",
                "role": "job_seeker",
            },
        )
        seeker1.set_password("password123")
        seeker1.save()

        seeker2, _ = User.objects.get_or_create(
            username="seeker2",
            defaults={
                "email": "seeker2@example.com",
                "role": "job_seeker",
            },
        )
        seeker2.set_password("password123")
        seeker2.save()

        company, _ = Company.objects.get_or_create(
            owner=employer,
            defaults={
                "name": "Acme Inc",
                "website": "https://example.com",
                "description": "A sample company for the job board project.",
            },
        )

        job1, _ = Job.objects.get_or_create(
            company=company,
            title="Junior Python Developer",
            defaults={
                "location": "Remote",
                "description": "Build and maintain backend services using Django.",
                "is_active": True,
            },
        )
        job2, _ = Job.objects.get_or_create(
            company=company,
            title="Frontend Intern (React)",
            defaults={
                "location": "Cairo (Hybrid)",
                "description": "Help build a responsive UI using Bootstrap and React.",
                "is_active": True,
            },
        )

        Application.objects.get_or_create(
            job=job1,
            applicant=seeker1,
            defaults={
                "cover_letter": "I'm excited to apply and learn on the job!",
            },
        )
        Application.objects.get_or_create(
            job=job1,
            applicant=seeker2,
            defaults={
                "cover_letter": "I have built small Django projects and would love to join.",
            },
        )
        Application.objects.get_or_create(
            job=job2,
            applicant=seeker1,
            defaults={
                "cover_letter": "I enjoy frontend work and want to grow my React skills.",
            },
        )

        self.stdout.write(self.style.SUCCESS("Seeded test data successfully."))

