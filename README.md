#  Django Job Board

A full-stack job board platform built with Django and PostgreSQL. Employers can post and manage job listings, while job seekers can browse, search, save, and apply — with email notifications throughout.

[![CI](https://github.com/HaymiG/django_job_board/actions/workflows/ci.yml/badge.svg)](https://github.com/HaymiG/django_job_board/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.12%2B-blue?style=flat-square&logo=python)
![Django](https://img.shields.io/badge/Django-6.x-green?style=flat-square&logo=django)
![DRF](https://img.shields.io/badge/DRF-3.16-red?style=flat-square&logo=django)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue?style=flat-square&logo=postgresql)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-purple?style=flat-square&logo=bootstrap)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker)

---

##  Features

### For Job Seekers
- Browse, search, and filter active job listings (keyword, type, category, location)
- Apply to jobs with a cover letter and PDF resume upload
- **Save / bookmark** jobs and view them on a dedicated Saved Jobs page
- Track application status (Submitted → Reviewing → Accepted / Rejected)
- Personal dashboard with application stats
- Receive confirmation emails on registration and every application

### For Employers
- Post, edit, and delete job listings
- View all applicants per job with status management
- **Analytics dashboard** — application counts, page views, and Chart.js charts
- Receive email notifications when a new application arrives

### Platform
- Two user roles — **Employer** and **Job Seeker** with role-based access control
- REST API with token authentication and a browsable API interface
- Dark / light mode toggle
- Responsive UI — works on mobile and desktop

---

##  Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 6, Python 3.12 |
| Database | PostgreSQL 16 |
| Frontend | Bootstrap 5.3, HTML, Vanilla CSS |
| API | Django REST Framework 3.16 |
| Charts | Chart.js 4 |
| Email | Django email backend (console / Gmail SMTP) |
| File Storage | Django MEDIA files |
| Web Server | Gunicorn + Nginx |
| Containerization | Docker + Docker Compose |
| Static Files | Whitenoise (with Brotli/gzip compression) |
| CI/CD | GitHub Actions |

---

##  Docker Quick Start

The fastest way to run the full stack (Django + PostgreSQL + Nginx) locally:

```bash
# 1. Clone and enter the project
git clone https://github.com/HaymiG/django_job_board.git
cd django_job_board

# 2. Copy the Docker env file and set your secret key
cp .env.docker .env.docker.local
# Edit .env.docker.local and set DJANGO_SECRET_KEY to something random

# 3. Start the stack (builds the image on first run)
docker compose up --build

# The app is now running at http://localhost:8000  (dev server, auto-reload)
# Nginx + Gunicorn (production mode):  http://localhost:80

# 4. Create a superuser (in a second terminal)
docker compose exec web python manage.py createsuperuser
```

### Useful Docker commands

```bash
# Start in the background
docker compose up -d

# View Django logs
docker compose logs -f web

# Run Django management commands
docker compose exec web python manage.py shell
docker compose exec web python manage.py migrate

# Run the test suite inside the container
docker compose exec web python manage.py test accounts jobs

# Stop everything (data is preserved in volumes)
docker compose down

# Stop and WIPE the database
docker compose down -v
```

### Stack architecture

```
[Browser]
    │ :80
    ▼
[Nginx]  ──/static/──▶  staticfiles volume
    │    ──/media/───▶   media volume
    │  proxy_pass
    ▼
[Gunicorn :8000]  (Django app — 3 workers)
    │
    ▼
[PostgreSQL :5432]  (named volume: postgres_data)
```

##  Getting Started

### Prerequisites

- Python 3.12+
- PostgreSQL
- Git

### 1. Clone the repository

```bash
git clone https://github.com/HaymiG/django_job_board.git
cd django-job-board
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate         # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

Copy the example file and fill in your values:

```bash
cp .env.example .env
```

`.env` reference:

```bash
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=1
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_ENGINE=postgres
DB_NAME=jobboard
DB_USER=jobboard_user
DB_PASSWORD=yourpassword
DB_HOST=127.0.0.1
DB_PORT=5432

# Email — console prints to terminal (no config needed in dev)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
DEFAULT_FROM_EMAIL=JobBoard <noreply@jobboard.local>

# To use real Gmail delivery instead:
# EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
# EMAIL_HOST=smtp.gmail.com
# EMAIL_PORT=587
# EMAIL_USE_TLS=1
# EMAIL_HOST_USER=you@gmail.com
# EMAIL_HOST_PASSWORD=your-16-char-app-password
# DEFAULT_FROM_EMAIL=JobBoard <you@gmail.com>
```

### 5. Create the database

```bash
psql -U postgres -c "CREATE DATABASE jobboard;"
psql -U postgres -c "CREATE USER jobboard_user WITH PASSWORD 'yourpassword';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE jobboard TO jobboard_user;"
```

### 6. Run migrations and create a superuser

```bash
python manage.py migrate
python manage.py createsuperuser
```

### 7. Run the development server

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000` in your browser.

---

##  Project Structure

```
django-job-board/
├── config/                  # Project config (settings, urls, wsgi)
│   ├── settings.py
│   └── urls.py
├── jobs/                    # Job listings, applications, search, saves
│   ├── api/                 # REST API (DRF ViewSets, serializers, router)
│   │   ├── serializers.py
│   │   ├── views.py
│   │   └── urls.py
│   ├── emails.py            # Email sending helpers
│   ├── context_processors.py # Saved jobs badge count
│   ├── models.py            # Job, Application, Company
│   ├── views.py
│   └── urls.py
├── accounts/                # Auth, user roles, dashboards, analytics
│   ├── models.py            # Custom User with role field
│   ├── views.py
│   ├── decorators.py
│   └── urls.py
├── templates/
│   ├── base.html
│   ├── jobs/
│   │   ├── home.html
│   │   ├── job_list.html
│   │   ├── job_detail.html
│   │   └── saved_jobs.html
│   ├── accounts/
│   │   ├── employer_dashboard.html
│   │   ├── employer_analytics.html
│   │   └── job_seeker_dashboard.html
│   └── emails/              # HTML email templates
│       ├── base_email.html
│       ├── registration_confirmation.html
│       ├── application_confirmation.html
│       └── employer_notification.html
├── static/
│   ├── css/site.css
│   └── js/theme.js
├── media/                   # Uploaded resumes
├── .env                     # Local environment variables (not committed)
├── .env.example             # Template for .env
├── requirements.txt
└── manage.py
```

---

##  API Reference

Base URL: `/api/`

Authentication: `Authorization: Token <your-token>`

### Get a token

```bash
POST /api/auth/token/
Content-Type: application/x-www-form-urlencoded

username=alice & password=secret
# Returns: {"token": "9944b09199c62bcf..."}
```

### Jobs

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/api/jobs/` | No | List all active jobs (paginated) |
| `GET` | `/api/jobs/{id}/` | No | Single job detail (increments view counter) |
| `POST` | `/api/jobs/{id}/save/` | Yes | Toggle bookmark this job |

**Query params:** `?search=python` · `?job_type=full_time` · `?category=technology` · `?location=remote` · `?ordering=-views`

### Applications

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/api/applications/` | Yes | My applications |
| `POST` | `/api/applications/` | Yes | Submit a new application |
| `GET` | `/api/applications/{id}/` | Yes | Single application detail |
| `DELETE` | `/api/applications/{id}/` | Yes | Withdraw an application |

### Browsable API

Visit `http://localhost:8000/api/` in your browser for the interactive DRF interface.

---

##  Email Notifications

Three emails are sent automatically:

| Trigger | Recipient | Template |
|---|---|---|
| User registers | New user | `registration_confirmation.html` |
| Job seeker applies | Applicant | `application_confirmation.html` |
| Job seeker applies | Employer | `employer_notification.html` |

In development, emails print to the terminal (no SMTP needed). Switch to Gmail for real delivery — see `.env.example` for the full configuration.

---

##  Running Tests

### Run the full test suite

```bash
python manage.py test accounts jobs --verbosity=2
```

### Run with coverage report

```bash
coverage run --source='.' manage.py test accounts jobs
coverage report --show-missing   # terminal summary
coverage html                    # open htmlcov/index.html in a browser
```

### Test suite overview

| Module | File | What is tested |
|---|---|---|
| `accounts` | `tests/test_models.py` | User creation, roles, defaults |
| `accounts` | `tests/test_auth.py` | Register, login (role redirect), logout |
| `accounts` | `tests/test_views.py` | Profile, employer/seeker dashboards, analytics, permissions |
| `jobs` | `tests/test_models.py` | Company, Job, Application models; constraints; M2M |
| `jobs` | `tests/test_views.py` | Home, job list (search/filter), detail, create, edit, delete |
| `jobs` | `tests/test_applications.py` | Apply, view applicants, update status, permission boundaries |
| `jobs` | `tests/test_saved_jobs.py` | Toggle save (regular + AJAX), saved list, isolation |

---

##  Analytics

Employers have access to a dedicated analytics page at `/accounts/dashboard/employer/analytics/` with:

- Total views and applications across all jobs
- Bar chart — applications per job
- Doughnut chart — application status breakdown
- Line chart — page views per job
- Ranking tables for top jobs by applications and views