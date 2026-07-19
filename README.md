# Seysmologiya instituti — xodimlar reyestri

A public staff registry for the Institute of Seismology (Uzbekistan). Anyone
can search and view employee profiles without an account. Only employees
register (with email verification); once verified, a profile is immediately
and permanently public — there is no admin approval step and no
visibility toggle.

- **Backend:** Django 6 + DRF, JWT auth (`djangorestframework-simplejwt`), PostgreSQL, Pillow
- **Frontend:** React 18 (Vite), React Router, Axios, **Tailwind CSS v4**, React Context for session state
- **UI language:** Uzbek (`frontend/src/i18n/uz.js`)

```
seismology-staff-registry/
├── docker-compose.yml
├── backend/     Django project (API)
└── frontend/    React app (Vite)
```

## Assumptions

- Login accepts **username OR email** in one field.
- **No admin approval workflow.** Earlier versions of this project had a
  pending/approved/rejected moderation step; that has been removed
  entirely. A verified, active account's profile is always public — the
  only gate is email verification.
  - The `is_public`, `moderation_status`, and `rejection_reason` **columns
    still exist in the database** (kept to avoid a migration), but the
    application no longer reads or writes them anywhere. They're
    effectively dead columns.
  - The Django admin no longer has approve/reject actions or
    moderation-related list filters/fields for `SpecialistProfile`.
- **Department is a real dropdown**, admin-managed — not free text.
- `research_interests` is collected at registration; `bio` is dashboard-only.
- **Documents are researchers' published articles, not just credential
  files.** Upload is (a) dashboard-only, never at registration (enforced on
  both frontend and backend), (b) PDF-only for security, (c) unlimited in
  count, and (d) shown on the **public** detail page (with download links)
  for every verified employee — this deliberately overrides the original
  "never expose raw documents" idea, since these files are meant to be
  discoverable, not just credentials for review.
- Implemented optional enhancement: **`ALLOWED_EMAIL_DOMAIN`** (restrict
  registration to a corporate domain). Not implemented (listed as future
  work below): ORCID/Scholar/Scopus + publications list, a "Bo'limlar"
  browse page, a language switcher, and Excel export.
- **State management: React Context**, not Redux Toolkit — the shared state
  (session + which modal is open) is small enough that Context avoids extra
  dependency weight without losing anything at this scale.
- **Tailwind CSS v4** (current stable) — CSS-first config via `@theme` in
  `frontend/src/styles/index.css`, using the `@tailwindcss/vite` plugin.
  No `tailwind.config.js` / `postcss.config.js` needed.

## Design plan

- **Palette:** `ink` #0F2A43 (headers/text), `ink-soft` #4B5C72, `sand` #B8863A
  (accent/CTAs), `sand-dark` #8E6526 (hover), `paper` #FAFAF8 (background),
  `surface` #FFFFFF (cards), plus `success`/`warning`/`danger` for alerts.
- **Type:** **Fraunces** (display serif, hero + section titles only) paired
  with **Inter** (body/UI). 8px spacing rhythm.
- **Signature element:** a static SVG **seismogram waveform** trace
  (`components/Seismogram.jsx`) under the hero title and above the footer,
  with a subtle draw-in animation on load (disabled under
  `prefers-reduced-motion`). Everything else stays quiet and disciplined.

---

## Option A — Run with Docker (recommended)

```bash
git clone <this-repo>
cd seismology-staff-registry
docker compose up --build
```

This starts PostgreSQL (`localhost:5432`), the Django backend
(`http://localhost:8000`, migrations run automatically), and the React
frontend (`http://localhost:5173`).

Create an admin and seed sample data in a second terminal:

```bash
docker compose exec backend python manage.py createsuperuser
docker compose exec backend python manage.py seed_data
```

Open `http://localhost:5173`.

## Option B — Run without Docker

### Prerequisites
Python 3.11+, Node.js 18+, PostgreSQL 14+ running locally.

### 1. Create the database

```bash
psql -U postgres
```
```sql
CREATE DATABASE seismology_registry;
CREATE USER seismology_registry WITH PASSWORD 'seismology_registry';
GRANT ALL PRIVILEGES ON DATABASE seismology_registry TO seismology_registry;
ALTER DATABASE seismology_registry OWNER TO seismology_registry;
```

### 2. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# edit .env if your DB credentials differ

python manage.py migrate
python manage.py createsuperuser
python manage.py seed_data                    # departments (no demo employees)

python manage.py runserver                     # http://localhost:8000
```

Django admin: `http://localhost:8000/admin/`.

### 3. Frontend

```bash
cd frontend
npm install

cp .env.example .env
# edit .env if your backend isn't on http://localhost:8000

npm run dev                                     # http://localhost:5173
```

---

## Environment variables

### `backend/.env`

| Variable | Default | Notes |
|---|---|---|
| `DEBUG` | `True` | |
| `SECRET_KEY` | — | set a real random value outside dev |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | comma-separated |
| `DB_NAME` / `DB_USER` / `DB_PASSWORD` / `DB_HOST` / `DB_PORT` | `seismology_registry` / … / `5432` | |
| `FRONTEND_ORIGIN` | `http://localhost:5173` | CORS allow-list |
| `EMAIL_BACKEND` | console backend | switch to SMTP for real email |
| `EMAIL_HOST` / `EMAIL_PORT` / `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` / `EMAIL_USE_TLS` | — | SMTP settings (production) |
| `DEFAULT_FROM_EMAIL` | `no-reply@seismology-institute.local` | |
| `ACCESS_TOKEN_LIFETIME_MINUTES` | `15` | |
| `REFRESH_TOKEN_LIFETIME_DAYS` | `7` | |
| `ALLOWED_EMAIL_DOMAIN` | *(blank = any domain)* | e.g. `seismology.uz` to restrict registration |

### `frontend/.env`

| Variable | Default |
|---|---|
| `VITE_API_BASE_URL` | `http://localhost:8000/api` |

## How email verification works in development

`EMAIL_BACKEND` defaults to Django's **console backend** — the verification
code prints straight into the terminal running `runserver` (or
`docker compose logs -f backend`):

```
Tasdiqlash kodingiz: 048213
Kod 15 daqiqadan so'ng amal qilishdan to'xtaydi.
```

**Flow:**
1. Employee registers → account is inactive, email unverified.
2. Employee enters the 6-digit code → account becomes active/verified.
3. **The profile is immediately public.** No admin step. The employee can
   log in right away and their profile shows up in search right away.

## Demo credentials

After `python manage.py seed_data` (departments only — no demo employees
are created; register real accounts through the site to test the full flow).

Admin account: whatever you set with `python manage.py createsuperuser`.

## Running backend tests

```bash
cd backend
python manage.py test
```

Covers: registration + verification (inactive → active/verified), login
(username, email, wrong password, unverified blocked), public search
(no auth required, name/department filters, unverified accounts never
appear, verified accounts appear regardless of the legacy `is_public`/
`moderation_status` column values), public detail (never exposes
email/username; uploaded documents ARE public), and document upload
(PDF-only, no count cap, dashboard-only — the register endpoint rejects
any `documents` field).

---

## API reference

All endpoints are prefixed with `/api/`.

| Method | Path | Auth | Notes |
|---|---|---|---|
| GET | `/departments/` | Public | dropdown source |
| GET | `/specialists/?name=&department=&page=` | Public (60/min) | every verified, active employee |
| GET | `/specialists/{id}/` | Public (60/min) | same |
| POST | `/auth/register/` | Public | multipart, one request (incl. photo; documents are dashboard-only) |
| POST | `/auth/verify-email/` | Public | `{email, code}` |
| POST | `/auth/resend-code/` | Public | 60s cooldown, 5/hour |
| POST | `/auth/login/` | Public | `{login, password}` → JWT |
| POST | `/auth/refresh/` | Public | `{refresh}` → new access |
| GET | `/me/` | JWT | basic account info |
| GET/PATCH | `/specialists/me/` | JWT, verified | own profile, photo replace/remove |
| POST | `/specialists/me/documents/` | JWT, verified | one PDF/request, unlimited count |
| DELETE | `/specialists/me/documents/{id}/` | JWT, verified | own file only |

## Future work (per section 10 of the original spec)

- ORCID / Google Scholar / Scopus links + a publications list on the profile.
- A "Bo'limlar" browse page listing departments with their staff.
- Language switcher (uz / ru / en) — the `i18n/uz.js` structure is ready for it.
- Admin action to export the staff list to Excel (openpyxl).

---

## Manual testing checklist

1. Open `http://localhost:5173` — centered hero with the seismogram motif,
   search console (name + department), logo top-left, Kirish/Ro'yxatdan
   o'tish top-right.
2. Search by name and separately by department — results filter correctly
   without logging in.
3. Click a result card → `/specialists/:id` shows photo, degree/title/position,
   department, research interests, bio, and any uploaded documents (as
   download links) — no email/username visible.
4. Click **"Ro'yxatdan o'tish"** → modal opens over the home page. Fill the
   form, attach a photo (see the live circular preview), submit.
5. Modal advances to the code step — check the backend console for the
   6-digit code, enter it → success screen.
6. Search for that employee's name **immediately** — they already appear,
   no admin action needed.
7. Click **"Kirish"**, log in with the new account → redirected to
   `/dashboard`.
8. Edit the profile and replace the photo (upload a new one, see the
   preview swap); save — confirm the change persists on reload.
9. Upload a PDF document from the dashboard, confirm it's PDF-only (try a
   non-PDF file, see it rejected), then delete it.
10. Visit that employee's public detail page again — the uploaded document
    appears there too.
11. Visit a nonsense URL like `/foo/bar` → the 404 page.
