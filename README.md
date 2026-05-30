# Ahoum Events Platform

Backend for a wellness events platform with JWT auth, email OTP verification, RBAC (Seeker / Facilitator), event search, and enrollments.

## Quick Start

```bash
npm run dev
```

Requires Docker Desktop. This starts PostgreSQL, Redis, Django, and Celery, runs migrations, and seeds sample data.

**Reset database after model changes:**

```bash
npm run stop
docker compose down -v
npm run dev
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Django secret key |
| `DEBUG` | Debug mode (`True` locally) |
| `DATABASE_URL` | PostgreSQL connection URL |
| `REDIS_URL` | Redis URL (OTP storage, cache, Celery) |
| `ALLOWED_HOSTS` | Comma-separated allowed hosts |

Copy `.env.example` to `.env` if needed.

## Design Decisions & Tradeoffs

- **Default User model** — assignment requirement; `username` is set internally to `email`.
- **OTP via Redis** — 6-digit code, 10-minute TTL, max 5 attempts. Logged to console in dev (no SMTP) so you can copy from Docker logs.
- **Profile model** — stores role separately from User for clean RBAC without custom user model.
- **UUID primary keys** — for Event and Enrollment to avoid predictable IDs in APIs.
- **Optional event capacity** — `null` capacity means unlimited seats.
- **Celery scheduled emails (bonus)** — follow-up 1 hour after enrollment and reminder 1 hour before event start; logged to worker console.
- **Error format** — `{"detail": "...", "code": "..."}` per assignment spec.

## Running Tests

```bash
docker compose exec web python manage.py test
```

Or locally with venv + Postgres/Redis running:

```bash
python manage.py test
```

## API Documentation

Import **`postman/Ahoum.postman_collection.json`** into Postman.

Optional Swagger UI: http://localhost:8000/api/docs/

## Auth Flow

1. `POST /api/auth/signup/` — `{email, password, role}` → OTP logged to server
2. `POST /api/auth/verify-email/` — `{email, otp}` → activates account
3. `POST /api/auth/login/` — `{email, password}` → `{access, refresh}` JWT tokens
4. `POST /api/auth/refresh/` — rotate refresh token

Unverified users cannot log in.

## Endpoints

### Auth

| Method | Endpoint | Auth |
|--------|----------|------|
| POST | `/api/auth/signup/` | Public |
| POST | `/api/auth/verify-email/` | Public |
| POST | `/api/auth/login/` | Public |
| POST | `/api/auth/refresh/` | Public |
| GET | `/api/auth/me/` | JWT |

### Events

| Method | Endpoint | Auth |
|--------|----------|------|
| GET | `/api/events/` | Public |
| POST | `/api/events/` | Facilitator |
| GET | `/api/events/<uuid>/` | Public |
| PUT/PATCH | `/api/events/<uuid>/` | Facilitator (owner) |
| DELETE | `/api/events/<uuid>/` | Facilitator (owner) → 204 |
| GET | `/api/events/my/` | Facilitator |

**Filters:** `q`, `language`, `location`, `starts_after`, `starts_before`

### Enrollments

| Method | Endpoint | Auth |
|--------|----------|------|
| POST | `/api/enrollments/` | Seeker |
| GET | `/api/enrollments/` | Seeker |
| GET | `/api/enrollments/?type=upcoming` | Seeker |
| GET | `/api/enrollments/?type=past` | Seeker |
| PATCH | `/api/enrollments/<uuid>/cancel/` | Seeker |
| GET | `/api/enrollments/event/<event_uuid>/` | Facilitator (owner) |

## Seed Data (pre-verified)

| Role | Email | Password |
|------|-------|----------|
| Facilitator | facilitator@ahoum.com | Test1234! |
| Seeker | seeker@ahoum.com | Test1234! |

## Docker Services

| Service | Role |
|---------|------|
| db | PostgreSQL 16 |
| redis | Cache + Celery broker + OTP |
| web | Django API |
| worker | Celery (emails) |

## Assignment Test Flow (Postman)

See `postman/Ahoum.postman_collection.json`. OTP appears in terminal logs:

```
EMAIL OTP for seeker2@ahoum.com: 123456 (expires in 600 seconds)
```

Look in the `web-1` container output after signup.
# Ahoum-Arkin
