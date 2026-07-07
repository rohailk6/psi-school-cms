# PSI School Examination CMS — Backend

FastAPI backend for the Pakistan Science Institute (PSI) School Examination CMS. Handles authentication/RBAC, academic years, classes & sections, students, teachers, exams, marks, and computed report cards.

## Tech Stack

- **FastAPI** + **Pydantic v2** — API layer & validation
- **SQLAlchemy 2.0** (async, via `asyncpg`) — ORM
- **Alembic** — migrations
- **PostgreSQL** — database
- **JWT** (access + refresh tokens) — auth

## Prerequisites

- Python 3.9+
- PostgreSQL running locally (or reachable)

## Setup

1. **Clone and create a virtualenv**
   ```bash
   git clone https://github.com/rohailk6/psi-school-cms.git
   cd psi-school-cms
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and set `SECRET_KEY`, `POSTGRES_*`, and `DATABASE_URL` / `DATABASE_URL_SYNC` to match your local Postgres setup.

3. **Create the database**
   ```bash
   createdb school_cms
   ```
   (Make sure the role in `DATABASE_URL` exists and owns/can access this database.)

4. **Run migrations**
   ```bash
   alembic upgrade head
   ```

5. **Seed roles, permissions, and a super admin**
   ```bash
   python -m app.db.seed
   ```
   Default admin (override via `SEED_ADMIN_EMAIL` / `SEED_ADMIN_PASSWORD` env vars):
   - Email: `admin@psi.edu.pk`
   - Password: `Admin@1234!`

   Change this password after first login.

6. **Run the server**
   ```bash
   uvicorn app.main:app --reload
   ```
   Server runs at `http://127.0.0.1:8000`.

## API Docs

Interactive Swagger UI (enabled when `DEBUG=True`):

```
http://127.0.0.1:8000/api/docs
```

1. `POST /api/v1/auth/login` with your email/password to get an `access_token`.
2. Click **Authorize** in Swagger and paste the token.
3. Try any endpoint.

Access tokens expire after 15 minutes — log in again to get a fresh one.

## Core Resources

| Resource | Base path |
|---|---|
| Auth | `/api/v1/auth` |
| Users | `/api/v1/users` |
| Roles | `/api/v1/roles` |
| Academic Years | `/api/v1/academic-years` |
| Classes & Sections | `/api/v1/classes` |
| Subjects | `/api/v1/subjects` |
| Students | `/api/v1/students` |
| Teachers | `/api/v1/teachers` |
| Exams & Marks | `/api/v1/exams` |
| Results / Report Cards | `/api/v1/results` |
| Dashboard | `/api/v1/dashboard` |

## Typical Workflow

1. Create an academic year, then activate it.
2. Create a class, then a section under that class.
3. Create a student and enroll them (class + section + academic year).
4. Create a teacher and assign them to a class/section/subject.
5. Create a subject.
6. Create an exam, attach a subject to it, then transition its status `draft → published` to allow mark entry.
7. Enter marks via `POST /api/v1/exams/exam-subjects/{exam_subject_id}/marks`.
8. Fetch the computed report card via `GET /api/v1/results/report-card/{student_id}/{exam_id}`.

## Migrations

Generate a new migration after changing models:
```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
```
