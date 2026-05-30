# Ahoum Events Platform — Backend (Done)

Complete description of the implemented Django REST API backend, aligned with the **Backend Task** assignment.

---

## 1. Overview

**Ahoum Events Platform** is a REST API for a wellness events marketplace:

- **Facilitators** create and manage events.
- **Seekers** search events, enroll, view enrollments, and cancel enrollments.
- **Authentication** uses JWT (access + refresh tokens) with email OTP verification before login.
- **RBAC** enforces role and resource ownership on every protected endpoint.

There is **no frontend** in this repository. Clients interact via HTTP (Postman, curl, etc.).

**Base URL (local):** `http://localhost:8000`

---

## 2. Tech Stack

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
| API docs (optional) | `drf-spectacular` (Swagger at `/api/docs/`) |
| Primary API docs | Postman collection (`postman/Ahoum.postman_collection.json`) |
| Production server | Gunicorn (Docker) |
| Local dev | `npm run dev` → Docker Compose |

---

## 3. User Model & Roles

### Default Django User

- Uses Django’s **built-in `User` model** (no custom user model).
- At signup, **`username` is set internally to `email`**.
- The signup API **does not accept** a `username` field.

### Profile (role storage)

| Field | Type | Description |
|-------|------|-------------|
| `user` | OneToOne → User | Linked account |
| `role` | `seeker` \| `facilitator` | RBAC role |
| `created_at` | DateTime | Auto |

### Roles

| Role | Capabilities |
|------|----------------|
| **seeker** | Search events, enroll, list/cancel own enrollments |
| **facilitator** | CRUD own events, list enrollments for own events |

---

## 4. Authentication & Email OTP

### Signup flow

1. **`POST /api/auth/signup/`** — creates an **inactive** user (`is_active=False`).
2. A **6-digit OTP** is generated, stored in **Redis** (10-minute TTL), and **logged to server console** (simulated email).
3. **`POST /api/auth/verify-email/`** — `{email, otp}` verifies the account (`is_active=True`).
4. **`POST /api/auth/login/`** — returns JWT tokens only if email is verified.

### OTP rules

| Setting | Value |
|---------|--------|
| TTL | 600 seconds (10 minutes) |
| Max attempts | 5 per OTP |
| Storage | Redis keys `otp:{email}`, `otp_attempts:{email}` |

### Login / tokens

| Endpoint | Body | Response |
|----------|------|----------|
| `POST /api/auth/login/` | `{email, password}` | `{access, refresh}` |
| `POST /api/auth/refresh/` | `{refresh}` | New access (+ rotated refresh) |
| `GET /api/auth/me/` | — (Bearer token) | User + profile |

**JWT lifetimes:** access 30 minutes, refresh 7 days, refresh rotation enabled.

**Authorization header:** `Authorization: Bearer <access_token>`

---

## 5. Domain Models

### Event

| Field | Type | Notes |
|-------|------|--------|
| `id` | UUID | Primary key |
| `title` | string (200) | |
| `description` | text | |
| `language` | string (50) | e.g. Hindi, English |
| `location` | string (255) | e.g. Mumbai |
| `starts_at` | DateTime (UTC) | |
| `ends_at` | DateTime (UTC) | Must be after `starts_at` |
| `capacity` | positive int, optional | `null` = unlimited seats |
| `created_by` | FK → User | Must be facilitator |
| `created_at` | DateTime | Auto |
| `updated_at` | DateTime | Auto |

**Indexes:** `starts_at`, `language`, `location`, `created_by`

**Default ordering:** `starts_at` ascending (upcoming first)

### Enrollment

| Field | Type | Notes |
|-------|------|--------|
| `id` | UUID | Primary key |
| `event` | FK → Event | |
| `seeker` | FK → User | Must be seeker |
| `status` | `enrolled` \| `canceled` | |
| `created_at` | DateTime | Auto |
| `updated_at` | DateTime | Auto |

**Business rules:**

- A seeker cannot have two **active** (`enrolled`) enrollments for the same event.
- Enrollment respects event **capacity** when set.
- Cannot enroll in events that have already ended.

---

## 6. RBAC & Permissions

Custom DRF permission classes (`apps/accounts/permissions.py`):

| Class | Purpose |
|-------|---------|
| `IsFacilitator` | User has facilitator role |
| `IsSeeker` | User has seeker role |
| `IsOwnerOrReadOnly` | Safe methods public; writes only if `created_by == request.user` |

---

## 7. API Endpoints

### Auth — `/api/auth/`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/signup/` | Public | Register; sends OTP to logs |
| POST | `/verify-email/` | Public | Verify OTP; activate account |
| POST | `/login/` | Public | JWT login (verified users only) |
| POST | `/refresh/` | Public | Refresh access token |
| POST | `/token/refresh/` | Public | Alias for refresh |
| GET | `/me/` | JWT | Current user + profile |

**Signup body:**

```json
{
  "email": "user@example.com",
  "password": "Test1234!",
  "role": "seeker"
}
```

---

### Events — `/api/events/`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/` | Public | Search & list (paginated) |
| POST | `/` | Facilitator | Create event (`created_by` = current user) |
| GET | `/<uuid>/` | Public | Event detail |
| PUT/PATCH | `/<uuid>/` | Facilitator (owner) | Update event |
| DELETE | `/<uuid>/` | Facilitator (owner) | Delete event → **204** |
| GET | `/my/` | Facilitator | Own events + enrollment stats |

**Create/update body:**

```json
{
  "title": "Morning Meditation",
  "description": "Guided session",
  "language": "Hindi",
  "location": "Mumbai",
  "starts_at": "2026-08-01T09:00:00Z",
  "ends_at": "2026-08-01T11:00:00Z",
  "capacity": 20
}
```

**List filters (query params):**

| Param | Description |
|-------|-------------|
| `q` | Search `title` and `description` (case-insensitive) |
| `language` | Exact match (case-insensitive) |
| `location` | Contains match |
| `starts_after` | `starts_at >=` value |
| `starts_before` | `starts_at <=` value |

**Ordering:** `?ordering=starts_at` (default), `created_at`

**Pagination:** 20 per page — `{count, next, previous, results}`

**My events response includes:** `total_enrollments`, `available_seats` (null if unlimited capacity)

---

### Enrollments — `/api/enrollments/`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/` | Seeker | Enroll in event |
| GET | `/` | Seeker | List own enrollments |
| GET | `/?type=upcoming` | Seeker | Future enrolled events |
| GET | `/?type=past` | Seeker | Past events (by `ends_at`) |
| PATCH | `/<uuid>/cancel/` | Seeker | Cancel own enrollment |
| GET | `/event/<event_uuid>/` | Facilitator (owner) | Enrollments for own event |

**Enroll body:**

```json
{
  "event": "<event-uuid>"
}
```

---

## 8. Error Response Format

All API errors use:

```json
{
  "detail": "Human-readable message",
  "code": "machine_readable_code"
}
```

**Example codes:** `validation_error`, `permission_denied`, `not_found`, `invalid_otp`, `otp_expired`, `max_otp_attempts`, `already_canceled`, `server_error`

---

## 9. Celery Background Tasks (Bonus)

Worker: `celery -A ahoum worker` (Docker service `worker`)

| Task | Trigger | Behavior |
|------|---------|----------|
| `send_enrollment_confirmation` | On enroll | Logs confirmation to console |
| `send_followup_email` | 1 hour after enroll | Logs follow-up (simulated email) |
| `send_event_reminder` | 1 hour before event start | Logs reminder (simulated email) |

No real SMTP — all emails are **logged** for development/demo.

---

## 10. Database

| Item | Value |
|------|--------|
| Engine | PostgreSQL 16 |
| Docker service | `db` |
| Database name | `ahoum` |
| User / password | `postgres` / `postgres` |
| Connection (in Docker) | `postgres://postgres:postgres@db:5432/ahoum` |
| Data persistence | Docker volume `ahoum_postgres_data` |

**Migrations:** `apps/accounts`, `apps/events`, `apps/enrollments` (initial migrations included).

**Redis:** Docker service `redis` — OTP storage, Django cache, Celery broker.

---

## 11. Docker Architecture

| Service | Image / command | Port |
|---------|-----------------|------|
| `db` | `postgres:16` | Internal only |
| `redis` | `redis:7-alpine` | Internal only |
| `web` | Gunicorn / `runserver` (dev) | `8000` → host |
| `worker` | `celery -A ahoum worker` | — |

**Local dev:** `npm run dev` runs Compose with `docker-compose.dev.yml` (migrations + seed on startup).

---

## 12. Project Structure

```
ahoum/                          # Django project
  settings/
    base.py                     # Shared settings
    local.py                    # Local overrides
    production.py               # Production overrides
  urls.py
  celery.py
  exception_handler.py
  exceptions.py
apps/
  accounts/                     # Auth, Profile, OTP, permissions
    models.py
    serializers.py
    views.py
    urls.py
    permissions.py
    otp.py
    tests.py
  events/                       # Event CRUD + search
    models.py
    serializers.py
    views.py
    urls.py
    filters.py
  enrollments/                  # Enrollments + Celery tasks
    models.py
    serializers.py
    views.py
    urls.py
    tasks.py
manage.py
seed.py
requirements.txt
docker-compose.yml
docker-compose.dev.yml
Dockerfile
.env.example
package.json                    # npm run dev
postman/
  Ahoum.postman_collection.json
README.md
done.md                         # This file
```

---

## 13. Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | Yes | Django secret |
| `DEBUG` | Yes | `True` locally |
| `DATABASE_URL` | Yes | PostgreSQL URL |
| `REDIS_URL` | Yes | Redis URL |
| `ALLOWED_HOSTS` | Yes | Comma-separated hosts |

---

## 14. How to Run

```bash
npm run dev
```

- API: http://localhost:8000/api/
- Swagger: http://localhost:8000/api/docs/
- Admin: http://localhost:8000/admin/

**Reset database:**

```bash
npm run stop
docker compose down -v
npm run dev
```

**Run tests:**

```bash
docker compose exec web python manage.py test
```

---

## 15. Seed Data (pre-verified users)

| Role | Email | Password |
|------|-------|----------|
| Facilitator | `facilitator@ahoum.com` | `Test1234!` |
| Seeker | `seeker@ahoum.com` | `Test1234!` |

Also creates 3 sample events (Hindi/English, Mumbai/Delhi).

```bash
docker compose exec web python seed.py
```

---

## 16. Assignment Checklist

| Requirement | Status |
|-------------|--------|
| Django default User model | Done |
| Signup without `username` field | Done |
| Signup: email, password, role | Done |
| Email OTP + verify endpoint | Done |
| OTP TTL + attempt limits | Done |
| Unverified users blocked from login | Done |
| JWT access + refresh | Done |
| RBAC seeker / facilitator | Done |
| Event model (assignment fields) | Done |
| Enrollment model (enrolled/canceled) | Done |
| Search: q, language, location, starts_after/before | Done |
| Paginated lists, upcoming ordering | Done |
| Enroll with capacity check | Done |
| Duplicate active enrollment blocked | Done |
| type=upcoming / type=past enrollments | Done |
| Facilitator CRUD (owner only) | Done |
| Facilitator my events + counts | Done |
| PostgreSQL + migrations + indexes | Done |
| Error format `{detail, code}` | Done |
| README + Postman collection | Done |
| Docker | Done |
| Scheduled email tasks (bonus) | Done (logged) |
| Tests | Done (`apps/accounts/tests.py`) |

---

## 17. What This Backend Does Not Include

- Frontend / mobile app
- Real SMTP email delivery (OTP and notifications are console-logged)
- Public cloud deployment URL (bonus item — not deployed)
- Custom User model or username-based signup

---

*Document reflects the codebase as implemented for the Ahoum Backend Task assignment.*
