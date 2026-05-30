# Ahoum API — How to Test with Postman

Step-by-step guide to verify all assignment endpoints on the **live deployment**.

---

## Live API

| Item | Value |
|------|-------|
| **Base URL** | `https://ahoum-arkin.vercel.app` |
| **Swagger docs** | `https://ahoum-arkin.vercel.app/api/docs/` |
| **Postman collection** | Import `postman/Ahoum.postman_collection.json` |

---

## Seed accounts (pre-created, no OTP needed)

| Role | Email | Password |
|------|-------|----------|
| Seeker | `seeker@ahoum.com` | `Test1234!` |
| Facilitator | `facilitator@ahoum.com` | `Test1234!` |

---

## Postman setup

1. Import **`postman/Ahoum.postman_collection.json`** into Postman.
2. For any request that needs auth:
   - Go to **Authorization** tab
   - Type: **Bearer Token**
   - Token: paste the **`access`** value from login (starts with `eyJ`, no quotes)
3. For POST/PATCH with a body:
   - **Body** → **raw** → **JSON**
   - Header: `Content-Type: application/json`
4. JWT access tokens expire after **30 minutes** — login again if you get token errors.

---

## Step 1 — Login (get tokens)

Run both logins and save the `access` token from each response.

### Login Seeker

| | |
|---|---|
| **Method** | `POST` |
| **URL** | `https://ahoum-arkin.vercel.app/api/auth/login/` |
| **Auth** | None |

**Body:**
```json
{
  "email": "seeker@ahoum.com",
  "password": "Test1234!"
}
```

**Expected:** `200`
```json
{
  "access": "eyJ...",
  "refresh": "eyJ..."
}
```
→ Save **`access`** as seeker token.

---

### Login Facilitator

| | |
|---|---|
| **Method** | `POST` |
| **URL** | `https://ahoum-arkin.vercel.app/api/auth/login/` |
| **Auth** | None |

**Body:**
```json
{
  "email": "facilitator@ahoum.com",
  "password": "Test1234!"
}
```

**Expected:** `200` → Save **`access`** as facilitator token.

---

### Optional — Who am I?

| | |
|---|---|
| **Method** | `GET` |
| **URL** | `https://ahoum-arkin.vercel.app/api/auth/me/` |
| **Auth** | Bearer (seeker or facilitator token) |

**Expected:** `200` — returns user email and role.

---

## Step 2 — Get event UUID (needed for enroll / edit)

No auth required.

| | |
|---|---|
| **Method** | `GET` |
| **URL** | `https://ahoum-arkin.vercel.app/api/events/?q=meditation` |

**Expected:** `200` — copy `"id"` from the first item in `results`.

Example seed event:
```
30aa8a31-7324-4a72-8855-7f20f81c97d1  →  Morning Meditation in Hindi
```

Use this UUID wherever `<event_id>` appears below.

---

## Step 3 — Seeker searches events

No auth required for any of these.

### 3.1 Keyword search

| | |
|---|---|
| **Method** | `GET` |
| **URL** | `https://ahoum-arkin.vercel.app/api/events/?q=meditation` |

**Expected:** `200` — at least 1 result.

---

### 3.2 Filter by language

| | |
|---|---|
| **Method** | `GET` |
| **URL** | `https://ahoum-arkin.vercel.app/api/events/?language=Hindi` |

**Expected:** `200`

---

### 3.3 Filter by location

| | |
|---|---|
| **Method** | `GET` |
| **URL** | `https://ahoum-arkin.vercel.app/api/events/?location=Mumbai` |

**Expected:** `200`

---

### 3.4 Filter by start date

| | |
|---|---|
| **Method** | `GET` |
| **URL** | `https://ahoum-arkin.vercel.app/api/events/?starts_after=2025-06-01` |

**Expected:** `200`

---

## Step 4 — Seeker enrolls

Auth: **Bearer seeker token**

### 4.1 Enroll in an event

| | |
|---|---|
| **Method** | `POST` |
| **URL** | `https://ahoum-arkin.vercel.app/api/enrollments/` |
| **Auth** | Bearer seeker token |

**Body:**
```json
{
  "event": "30aa8a31-7324-4a72-8855-7f20f81c97d1"
}
```
*(Replace with your `<event_id>` from Step 2.)*

**Expected:** `201` — copy `"id"` from response as `<enrollment_id>`.

---

### 4.2 Enroll in same event again

Same as 4.1 (same URL, same body).

**Expected:** `400`
```json
{
  "detail": "You are already enrolled in this event.",
  "code": "validation_error"
}
```

---

### 4.3 Enroll as facilitator (should fail)

| | |
|---|---|
| **Method** | `POST` |
| **URL** | `https://ahoum-arkin.vercel.app/api/enrollments/` |
| **Auth** | Bearer **facilitator** token |

**Body:**
```json
{
  "event": "30aa8a31-7324-4a72-8855-7f20f81c97d1"
}
```

**Expected:** `403`
```json
{
  "detail": "Seeker role required.",
  "code": "permission_denied"
}
```

---

## Step 5 — Seeker views enrollments

Auth: **Bearer seeker token**

### 5.1 All enrollments

| | |
|---|---|
| **Method** | `GET` |
| **URL** | `https://ahoum-arkin.vercel.app/api/enrollments/` |

**Expected:** `200`

---

### 5.2 Upcoming enrollments

| | |
|---|---|
| **Method** | `GET` |
| **URL** | `https://ahoum-arkin.vercel.app/api/enrollments/?type=upcoming` |

**Expected:** `200`

---

### 5.3 Past enrollments

| | |
|---|---|
| **Method** | `GET` |
| **URL** | `https://ahoum-arkin.vercel.app/api/enrollments/?type=past` |

**Expected:** `200`

---

## Step 6 — Facilitator views event enrollments

### 6.1 Facilitator sees enrollments (should succeed)

| | |
|---|---|
| **Method** | `GET` |
| **URL** | `https://ahoum-arkin.vercel.app/api/enrollments/event/30aa8a31-7324-4a72-8855-7f20f81c97d1/` |
| **Auth** | Bearer **facilitator** token |

*(Replace UUID with your `<event_id>`.)*

**Expected:** `200` — should list `seeker@ahoum.com`.

---

### 6.2 Seeker tries same endpoint (should fail)

| | |
|---|---|
| **Method** | `GET` |
| **URL** | `https://ahoum-arkin.vercel.app/api/enrollments/event/30aa8a31-7324-4a72-8855-7f20f81c97d1/` |
| **Auth** | Bearer **seeker** token |

**Expected:** `403`
```json
{
  "detail": "Facilitator role required.",
  "code": "permission_denied"
}
```

---

## Step 7 — Cancel enrollment

Auth: **Bearer seeker token**

| | |
|---|---|
| **Method** | `PATCH` |
| **URL** | `https://ahoum-arkin.vercel.app/api/enrollments/<enrollment_id>/cancel/` |
| **Auth** | Bearer seeker token |
| **Body** | None |

Example:
```
https://ahoum-arkin.vercel.app/api/enrollments/b5657f41-123d-4684-a8ae-b931bcf7e401/cancel/
```
*(Use `<enrollment_id>` from Step 4.1.)*

**Expected:** `200`
```json
{
  "id": "...",
  "status": "canceled",
  ...
}
```

---

## Step 8 — Facilitator edits and deletes events

Auth: **Bearer facilitator token** (except where noted)

### 8.1 Create a test event (to avoid deleting seed data)

| | |
|---|---|
| **Method** | `POST` |
| **URL** | `https://ahoum-arkin.vercel.app/api/events/` |
| **Auth** | Bearer facilitator token |

**Body:**
```json
{
  "title": "Test Event For Delete",
  "description": "Temporary event for Step 8 testing.",
  "language": "English",
  "location": "Mumbai",
  "starts_at": "2026-09-01T09:00:00Z",
  "ends_at": "2026-09-01T11:00:00Z",
  "capacity": 10
}
```

**Expected:** `201` — copy `"id"` as `<delete_event_id>`.

---

### 8.2 Update event (facilitator)

| | |
|---|---|
| **Method** | `PATCH` |
| **URL** | `https://ahoum-arkin.vercel.app/api/events/<delete_event_id>/` |
| **Auth** | Bearer facilitator token |

**Body:**
```json
{
  "title": "Test Event For Delete (Updated)"
}
```

**Expected:** `200`

---

### 8.3 Update event as seeker (should fail)

| | |
|---|---|
| **Method** | `PATCH` |
| **URL** | `https://ahoum-arkin.vercel.app/api/events/<delete_event_id>/` |
| **Auth** | Bearer **seeker** token |

**Body:**
```json
{
  "title": "Hacked Title"
}
```

**Expected:** `403`

---

### 8.4 Delete event (facilitator)

| | |
|---|---|
| **Method** | `DELETE` |
| **URL** | `https://ahoum-arkin.vercel.app/api/events/<delete_event_id>/` |
| **Auth** | Bearer facilitator token |
| **Body** | None |

**Expected:** `204` (empty response body)

---

### 8.5 Fetch deleted event (should fail)

| | |
|---|---|
| **Method** | `GET` |
| **URL** | `https://ahoum-arkin.vercel.app/api/events/<delete_event_id>/` |
| **Auth** | None |

**Expected:** `404`

---

## Bonus — Signup with OTP (optional)

Only needed if creating **new** users. Seed accounts skip this.

### Signup

| | |
|---|---|
| **Method** | `POST` |
| **URL** | `https://ahoum-arkin.vercel.app/api/auth/signup/` |

**Body:**
```json
{
  "email": "newseeker@ahoum.com",
  "password": "Test1234!",
  "role": "seeker"
}
```

**Expected:** `201` — OTP is logged in **Vercel Runtime Logs** (not local terminal).

---

### Verify email

| | |
|---|---|
| **Method** | `POST` |
| **URL** | `https://ahoum-arkin.vercel.app/api/auth/verify-email/` |

**Body:**
```json
{
  "email": "newseeker@ahoum.com",
  "otp": "123456"
}
```

Replace `123456` with OTP from Vercel logs.

**Expected:** `200` — then login with that email.

---

## Quick reference — all URLs

| Method | URL | Auth |
|--------|-----|------|
| POST | `/api/auth/login/` | None |
| POST | `/api/auth/signup/` | None |
| POST | `/api/auth/verify-email/` | None |
| GET | `/api/auth/me/` | JWT |
| GET | `/api/events/` | None |
| GET | `/api/events/?q=meditation` | None |
| GET | `/api/events/?language=Hindi` | None |
| GET | `/api/events/?location=Mumbai` | None |
| GET | `/api/events/?starts_after=2025-06-01` | None |
| POST | `/api/events/` | Facilitator |
| PATCH | `/api/events/<event_id>/` | Facilitator (owner) |
| DELETE | `/api/events/<event_id>/` | Facilitator (owner) |
| GET | `/api/events/my/` | Facilitator |
| POST | `/api/enrollments/` | Seeker |
| GET | `/api/enrollments/` | Seeker |
| GET | `/api/enrollments/?type=upcoming` | Seeker |
| GET | `/api/enrollments/?type=past` | Seeker |
| PATCH | `/api/enrollments/<enrollment_id>/cancel/` | Seeker |
| GET | `/api/enrollments/event/<event_id>/` | Facilitator (owner) |

Prefix every path with: `https://ahoum-arkin.vercel.app`

---

## Expected results checklist

| Step | Test | Expected status |
|------|------|-----------------|
| 1 | Login seeker | 200 |
| 1 | Login facilitator | 200 |
| 3 | Search q=meditation | 200 |
| 3 | Filter language=Hindi | 200 |
| 3 | Filter location=Mumbai | 200 |
| 3 | Filter starts_after | 200 |
| 4 | Enroll (seeker) | 201 |
| 4 | Enroll again | 400 |
| 4 | Enroll as facilitator | 403 |
| 5 | List enrollments | 200 |
| 5 | List upcoming | 200 |
| 5 | List past | 200 |
| 6 | Event enrollments (facilitator) | 200 |
| 6 | Event enrollments (seeker) | 403 |
| 7 | Cancel enrollment | 200, status=canceled |
| 8 | Update event (facilitator) | 200 |
| 8 | Update event (seeker) | 403 |
| 8 | Delete event | 204 |
| 8 | Get deleted event | 404 |

---

## Troubleshooting

| Error | Fix |
|-------|-----|
| `not_authenticated` | Add Bearer token with `access` from login |
| `token_not_valid` | Login again; paste full `eyJ...` token, no quotes |
| `Facilitator role required` | Wrong endpoint or wrong token for seeker flow |
| `Seeker role required` | Using facilitator token on enroll endpoint |
| `already enrolled` | Cancel enrollment first, or use a different event |
| `500` on enroll | Ensure latest code is deployed (Celery fix on Vercel) |

---

*Live API: https://ahoum-arkin.vercel.app*
