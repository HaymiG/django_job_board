#  Django Job Board
 
A full-stack job board platform built with Django and PostgreSQL. Employers can post and manage job listings, while job seekers can browse, search, and apply with resume uploads.
 
![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square&logo=python)
![Django](https://img.shields.io/badge/Django-5.x-green?style=flat-square&logo=django)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue?style=flat-square&logo=postgresql)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5-purple?style=flat-square&logo=bootstrap)
![Railway](https://img.shields.io/badge/Deployed-Railway-black?style=flat-square&logo=railway)
 
---
 
## 🔗 Live Demo
 
**[View Live App →](https://your-app.railway.app)**
 
---
 
## ✨ Features
 
- **Two user roles** — Employer and Job Seeker with role-based access control
- **Job listings** — Employers can post, edit, and delete job listings
- **Apply to jobs** — Seekers apply with a cover letter and PDF resume upload
- **Employer dashboard** — View all applicants per job listing
- **Search & filter** — Search by keyword, filter by job type and category
- **Pagination** — Clean paginated job listings
- **Authentication** — Register, login, logout with protected routes
- **REST API** — JSON endpoints built with Django REST Framework
- **Responsive UI** — Bootstrap 5, works on mobile and desktop
- **Email notifications** — Confirmation emails on registration and application
---
 
## 🛠 Tech Stack
 
| Layer | Technology |
|---|---|
| Backend | Django 5, Python 3.11 |
| Database | PostgreSQL |
| Frontend | Bootstrap 5, HTML, CSS |
| API | Django REST Framework |
| File Storage | Django MEDIA files |
| Deployment | Railway |
| Static Files | Whitenoise |
 
---
 
##  Screenshots
 
> *(Add screenshots here after deployment)*
 
---
 
## 🚀 Getting Started
 
### Prerequisites
 
- Python 3.11+
- PostgreSQL
- Git
### 1. Clone the repository
 
```bash
git clone https://github.com/your-username/django-job-board.git
cd django-job-board
```
 
### 2. Create and activate virtual environment
 
```bash
python -m venv venv
source venv/bin/activate        # Mac/Linux
# venv\Scripts\activate         # Windows
```
 
### 3. Install dependencies
 
```bash
pip install -r requirements.txt
```
 
### 4. Set up environment variables
 
Create a `.env` file in the root directory:
 
```
SECRET_KEY=your-secret-key-here
DEBUG=True
DATABASE_URL=postgres://postgres:password@localhost:5432/jobboard_db
```
 
### 5. Set up the database
 
```bash
psql -U postgres -c "CREATE DATABASE jobboard_db;"
python manage.py migrate
python manage.py createsuperuser
```
 
### 6. Run the development server
 
```bash
python manage.py runserver
```
 
Visit `http://127.0.0.1:8000` in your browser.
 
---
 
## 📁 Project Structure
 
```
django-job-board/
├── jobboard/          # Project config (settings, urls, wsgi)
├── jobs/              # Job listings, applications, search
├── accounts/          # Auth, user roles, profiles
├── templates/         # HTML templates
├── static/            # CSS, JS, images
├── media/             # Uploaded resumes and logos
├── requirements.txt
├── Procfile
└── manage.py
```
 
---
 
## 🔌 API Endpoints
 
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/jobs/` | List all active jobs |
| GET | `/api/jobs/:id/` | Get single job detail |
| POST | `/api/jobs/` | Create a job (employer only) |
| GET | `/api/applications/` | List user's applications |
| POST | `/api/applications/` | Submit an application |
 
Authentication via token — include `Authorization: Token <your-token>` in headers.
 
---
 
##  Running Tests
 
```bash
python manage.py test
```
 
---
 
##  Deployment
 
This app is deployed on [Railway](https://railway.app).
 
To deploy your own instance:
 
1. Push your code to GitHub
2. Create a new project on Railway
3. Add a PostgreSQL plugin
4. Set environment variables (`SECRET_KEY`, `DEBUG=False`)
5. Railway auto-deploys on every push
---
 
<!-- ## 🗓 Roadmap
 
- [x] User authentication & roles
- [x] Job CRUD
- [x] Application system with resume upload
- [x] Search & filters
- [x] Employer dashboard
- [x] REST API
- [x] Deployment
- [ ] Email notifications
- [ ] Saved jobs
- [ ] Docker support
- [ ] GitHub Actions CI/CD -->
<!-- --- -->
 
##  Author
 
**Your Name**
- GitHub: [@your-username](https://github.com/your-username)
- LinkedIn: [your-linkedin](https://linkedin.com/in/your-linkedin)
---
 
## 📄 License
 
This project is open source and available under the [MIT License](LICENSE).