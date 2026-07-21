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
- **Scientific works replace the old flat document list.** Every employee's
  publications live in one `ScientificWork` table across five categories
  (foreign articles, local articles, theses, patents, monographs), each
  with its own required/optional fields. A PDF is **required on every
  record in every category**, is **dashboard-only** to upload (never at
  registration), and once a profile is public (i.e. the account is
  verified), all of that employee's works — including the PDF download
  links — are public too. This deliberately overrides the original "never
  expose raw documents" idea, since these files are meant to be
  discoverable, not just credentials for review.
  - **Old `SpecialistDocument` rows were migrated**, not discarded: each
    became a `local_article` with `title` = the original filename
    (extension stripped) and `year` = the upload year — both are editable
    afterward. See `specialists/migrations/0003_migrate_documents_to_works.py`.
  - **File replace-only, no removal**: `PATCH` can swap the PDF, but a work
    can never end up without one.
  - **DOI duplicates** are a soft, confirmable warning (not a hard block)
    scoped per employee — two different employees may share a DOI freely.
  - **PDF validation** now includes a real `%PDF-` magic-byte check
    (dependency-free), catching a `.docx` renamed to `.pdf`.
  - Implemented optional enhancements: a **per-category summary** (total
    count) at the top of the dashboard's works section, and a **project-name
    autocomplete** (datalist, sourced from the employee's own prior
    entries). Listed as future work: DOI autofill via the Crossref API, and
    Excel export.
- Implemented optional enhancement: **`ALLOWED_EMAIL_DOMAIN`** (restrict
  registration to a corporate domain). Not implemented (listed as future
  work below): ORCID/Scholar/Scopus + publications list, a "Bo'limlar"
  browse page, and a language switcher.
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

## Upgrading an existing deployment

If you already have a running instance with employees who uploaded
documents under the old flat-list system, upgrading is just a normal
migration — **no manual data steps needed**:

```bash
git pull
docker compose up -d --build      # or: python manage.py migrate  (without Docker)
```

Migrations `0002` → `0004` run automatically in order: create the new
`ScientificWork` table, copy every old document into it as a
`local_article` (title = old filename, year = old upload year, same PDF
file — nothing is re-uploaded or lost), then drop the old table. This exact
sequence was tested against simulated production data before release.

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
`moderation_status` column values, cards include `works_count`), public
detail (never exposes email/username; includes `works_count` and
`works_by_category`), and scientific works (per-category required-field
validation, PDF-only + magic-byte enforcement, no count cap, file
replace-only on update, ownership isolation between employees, DOI
duplicate warning + confirm override, DOI reuse allowed across different
employees, public works endpoint scoped to verified employees with
category filtering).

---

## API reference

All endpoints are prefixed with `/api/`.

| Method | Path | Auth | Notes |
|---|---|---|---|
| GET | `/departments/` | Public | dropdown source |
| GET | `/specialists/?name=&department=&page=` | Public (60/min) | every verified, active employee; cards include `works_count` |
| GET | `/specialists/{id}/` | Public (60/min) | includes `works_count` + `works_by_category` |
| GET | `/specialists/{id}/works/?category=&page=&ordering=` | Public (60/min) | a specific verified employee's works |
| POST | `/auth/register/` | Public | multipart, one request (incl. photo; works are dashboard-only) |
| POST | `/auth/verify-email/` | Public | `{email, code}` |
| POST | `/auth/resend-code/` | Public | 60s cooldown, 5/hour |
| POST | `/auth/login/` | Public | `{login, password}` → JWT |
| POST | `/auth/refresh/` | Public | `{refresh}` → new access |
| GET | `/me/` | JWT | basic account info |
| GET/PATCH | `/specialists/me/` | JWT, verified | own profile, photo replace/remove |
| GET/POST | `/specialists/me/works/?category=&page=&ordering=` | JWT, verified | list/create own works, no count cap |
| GET/PATCH/DELETE | `/specialists/me/works/{id}/` | JWT, verified | edit (incl. PDF replace) or delete a single work |

**`ScientificWork` categories** (`category` field): `foreign_article`,
`local_article`, `thesis`, `patent`, `monograph`. Required fields differ per
category — see `specialists/serializers.py::ScientificWorkSerializer.CATEGORY_REQUIRED_FIELDS`.
A PDF file is required on create for every category; `PATCH` can replace it
but never remove it. A same-employee DOI duplicate returns
`{"code": "duplicate_doi", ...}` (400) unless the request also includes
`confirm_duplicate=true`.

## Future work (per section 10 of the seismology spec, and the scientific-works change request)

- ORCID / Google Scholar / Scopus links + a general publications list on the profile.
- A "Bo'limlar" browse page listing departments with their staff.
- Language switcher (uz / ru / en) — the `i18n/uz.js` structure is ready for it.
- "DOI orqali to'ldirish" auto-fill on the foreign/local article form via the Crossref API.
- Admin export of all scientific works to Excel with a category column (openpyxl).

---

## Manual testing checklist

1. Open `http://localhost:5173` — centered hero with the seismogram motif,
   search console (name + department), logo top-left, Kirish/Ro'yxatdan
   o'tish top-right.
2. Search by name and separately by department — results filter correctly
   without logging in; each card shows a total works count (e.g. "0 ta
   ilmiy ish" for a brand-new account).
3. Register a new employee, verify the email code, log in → `/dashboard`.
4. In **"Ilmiy ishlarim"**, add one record in each of the five categories
   (Xorijiy maqolalar, Mahalliy maqolalar, Tezislar, Patentlar,
   Monografiyalar) with a PDF attached each time — confirm the per-tab
   counts update immediately after each save.
5. Try saving a record **without** a PDF — confirm the "PDF fayl yuklash
   majburiy" error. Try a required text field left blank (e.g. a local
   article with no journal name) — confirm the field-level Uzbek error.
6. Click a sortable column header (e.g. "Yili") — confirm the sort order
   toggles; for Patentlar, confirm "Berilgan yili" displays as DD.MM.YYYY.
7. Edit one record's metadata without touching the file — confirm the PDF
   is unchanged. Edit another and replace its PDF — confirm the new file
   downloads correctly afterward.
8. Enter a DOI that already exists on one of your own records — confirm
   the "Bu DOI bilan yozuv allaqachon mavjud" confirm dialog appears, and
   that confirming saves it anyway.
9. Delete one record (confirm dialog) — confirm it disappears and the tab
   count decrements.
10. Open that employee's public profile (`/specialists/:id`) — confirm the
    same five tabs appear (only non-empty ones), same columns minus
    "Amallar", and every row's PDF downloads. Confirm no email/username is
    visible anywhere.
11. Back on the home page, search for that employee again — the card's
    total works count now reflects everything you added.
12. Visit a nonsense URL like `/foo/bar` → the 404 page.
