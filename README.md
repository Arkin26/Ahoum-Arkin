# Ahoum Events Platform

REST API backend for a **wellness events marketplace**. Facilitators create and manage events; seekers search, enroll, and manage their bookings. Authentication uses JWT with email OTP verification and role-based access control (RBAC).

There is **no frontend** in this repository — clients interact via HTTP (Postman, curl, etc.).

| Environment | Base URL |
|-------------|----------|
| **Live (production)** | https://ahoum-arkin.vercel.app |
| **Local (Docker)** | http://localhost:8000 |

**Quick links**

- **Postman testing guide:** [`how-to-use.md`](how-to-use.md) — step-by-step URLs, bodies, and expected responses
- **Postman collection:** [`postman/Ahoum.postman_collection.json`](postman/Ahoum.postman_collection.json)
- **Swagger UI:** https://ahoum-arkin.vercel.app/api/docs/ (local: http://localhost:8000/api/docs/)
- **Full technical write-up:** [`done.md`](done.md)

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Language | Python 3.12 |
| Framework | Django 5.x |
| API | Django REST Framework 3.15+ |
| Auth | `djangorestframework-simplejwt` (JWT) |
| Database | PostgreSQL 16 |
| Cache / OTP | Redis 7 (`django-redis`) |
| Async tasks | Celery + Redis broker |
| Config | `django-environ` (`.env`) |
| Filtering | `django-filter` |
| API docs | `drf-spectacular` (Swagger) |
| Local dev | Docker Compose (`npm run dev`) |
| Production | Vercel (Django) + Neon Postgres + Upstash Redis |

---

## How It Works

### User roles

Uses Django’s built-in `User` model. Roles are stored on a separate `Profile` model (`seeker` or `facilitator`). At signup, `username` is set internally to `email`.

| Role | What they can do |
|------|------------------|
| **Seeker** | Search events, enroll, list own enrollments, cancel enrollments |
| **Facilitator** | Create/update/delete own events, list enrollments for own events |

### Authentication flow

1. **`POST /api/auth/signup/`** — creates an inactive user; 6-digit OTP stored in Redis and logged to server console (simulated email)
2. **`POST /api/auth/verify-email/`** — `{email, otp}` activates the account
3. **`POST /api/auth/login/`** — returns `{access, refresh}` JWT tokens (verified users only)
4. **`POST /api/auth/refresh/`** — rotate refresh token

**JWT:** access token 30 min, refresh token 7 days, rotation enabled.

**Authorization header:** `Authorization: Bearer <access_token>`

### Core domain

**Event** — title, description, language, location, starts_at, ends_at, optional capacity, created_by (facilitator). UUID primary key.

**Enrollment** — links a seeker to an event with status `enrolled` or `canceled`. UUID primary key.

**Business rules**

- One active enrollment per seeker per event
- Respects event capacity when set (`null` capacity = unlimited)
- Cannot enroll in past events
- Facilitators can only modify/delete events they created

### Error format

All API errors return:

```json
{
  "detail": "Human-readable message",
  "code": "machine_readable_code"
}
```

Example codes: `validation_error`, `permission_denied`, `not_found`, `invalid_otp`, `token_not_valid`

### Background tasks (bonus)

Celery worker sends simulated emails (logged to console, no SMTP):

| Task | When |
|------|------|
| Enrollment confirmation | On enroll |
| Follow-up email | 1 hour after enroll |
| Event reminder | 1 hour before event start |

On Vercel (serverless), only the confirmation log runs inline — scheduled tasks require the Docker Celery worker locally.

---

## What's in This Repo

```
ahoum/                    # Django project (settings, urls, celery, exception handler)
apps/
  accounts/               # Auth, Profile, OTP, RBAC permissions
  events/                 # Event CRUD, search, filters
  enrollments/            # Enrollments, cancel, Celery email tasks
manage.py
seed.py                   # Sample users + events
postman/                  # Postman collection (live URLs)
how-to-use.md             # Postman testing guide for reviewers
done.md                   # Detailed technical documentation
docker-compose.yml        # Postgres, Redis, web, worker
requirements.txt
pyproject.toml            # Vercel deployment config
```

---

## API Endpoints

### Auth — `/api/auth/`

| Method | Endpoint | Auth |
|--------|----------|------|
| POST | `/signup/` | Public |
| POST | `/verify-email/` | Public |
| POST | `/login/` | Public |
| POST | `/refresh/` | Public |
| GET | `/me/` | JWT |

### Events — `/api/events/`

| Method | Endpoint | Auth |
|--------|----------|------|
| GET | `/` | Public (search & list) |
| POST | `/` | Facilitator |
| GET | `/<uuid>/` | Public |
| PUT/PATCH | `/<uuid>/` | Facilitator (owner) |
| DELETE | `/<uuid>/` | Facilitator (owner) → 204 |
| GET | `/my/` | Facilitator |

**Query filters:** `q`, `language`, `location`, `starts_after`, `starts_before`

### Enrollments — `/api/enrollments/`

| Method | Endpoint | Auth |
|--------|----------|------|
| POST | `/` | Seeker |
| GET | `/` | Seeker |
| GET | `/?type=upcoming` | Seeker |
| GET | `/?type=past` | Seeker |
| PATCH | `/<uuid>/cancel/` | Seeker |
| GET | `/event/<event_uuid>/` | Facilitator (owner) |

---

## Seed Data (pre-verified)

Use these on the live API — no OTP needed:

| Role | Email | Password |
|------|-------|----------|
| Facilitator | `facilitator@ahoum.com` | `Test1234!` |
| Seeker | `seeker@ahoum.com` | `Test1234!` |

Three sample events are seeded (meditation, wellness workshop, yoga).

---

## Quick Start (local)

**Requirements:** Docker Desktop

```bash
npm run dev
```

This starts PostgreSQL, Redis, Django, and Celery, runs migrations, and seeds sample data.

API available at **http://localhost:8000**

**Reset database after model changes:**

```bash
npm run stop
docker compose down -v
npm run dev
```

### Environment variables

Copy `.env.example` to `.env` if needed:

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Django secret key |
| `DEBUG` | Debug mode (`True` locally) |
| `DATABASE_URL` | PostgreSQL connection URL |
| `REDIS_URL` | Redis URL (OTP, cache, Celery) |
| `ALLOWED_HOSTS` | Comma-separated allowed hosts |

### Docker services

| Service | Role |
|---------|------|
| `db` | PostgreSQL 16 |
| `redis` | Cache + Celery broker + OTP |
| `web` | Django API (port 8000) |
| `worker` | Celery background tasks |

---

## Production Deployment

Deployed on **Vercel** with:

- **Neon** — PostgreSQL (pooled connection)
- **Upstash** — Redis (`rediss://` URL for OTP + cache)

Build runs migrations via `scripts/vercel-build.sh`. Set `SEED_ON_DEPLOY=1` on first deploy only.

---

## Testing the API

### Postman (recommended for reviewers)

1. Import [`postman/Ahoum.postman_collection.json`](postman/Ahoum.postman_collection.json)
2. Follow [`how-to-use.md`](how-to-use.md) for every step, URL, body, and expected status code

### Unit tests

```bash
docker compose exec web python manage.py test
```

---

## Design Decisions

- **Default User model** — assignment requirement; email-based signup without exposing `username`
- **OTP via Redis** — 6-digit code, 10-minute TTL, max 5 attempts; logged to console in dev
- **Profile model** — clean RBAC without a custom user model
- **UUID primary keys** — for Event and Enrollment
- **Optional event capacity** — `null` means unlimited seats
- **Standardized errors** — `{detail, code}` on every error response

---

## Assignment Test Flow

Full step-by-step with live URLs and JSON bodies: **[`how-to-use.md`](how-to-use.md)**

Summary:

1. Login seeker + facilitator
2. Search events (keyword, language, location, date filters)
3. Seeker enrolls → duplicate enroll (400) → facilitator enroll attempt (403)
4. Seeker lists enrollments (all, upcoming, past)
5. Facilitator views event enrollments (200) / seeker attempt (403)
6. Seeker cancels enrollment
7. Facilitator updates event (200) / seeker attempt (403) / delete event (204) / fetch deleted (404)

---

*Live API: https://ahoum-arkin.vercel.app*
