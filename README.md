# Seysmologiya instituti — xodimlar reyestri

A public staff registry for the Institute of Seismology (Uzbekistan). Anyone
can search and view employee profiles without an account. Only employees
register (with email verification); once verified, a profile is immediately
and permanently public — there is no admin approval step and no
visibility toggle.

- **Backend:** Django 6 + DRF, JWT auth (`djangorestframework-simplejwt`), PostgreSQL, Pillow, openpyxl, zipstream-ng
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
  publications live in one `ScientificWork` table across six categories
  (foreign articles, local articles, theses, conference participation,
  patents, other publications), each with its own required/optional fields.
  A PDF is **required on every record in every category except conference
  participation** (a certificate may arrive after the fact), is
  **dashboard-only** to upload (never at registration), and once a profile
  is public (i.e. the account is verified), all of that employee's works —
  including the PDF download links — are public too. This deliberately
  overrides the original "never expose raw documents" idea, since these
  files are meant to be discoverable, not just credentials for review.
  - **Old `SpecialistDocument` rows were migrated**, not discarded: each
    became a `local_article` with `title` = the original filename
    (extension stripped) and `year` = the upload year — both are editable
    afterward. See `specialists/migrations/0003_migrate_documents_to_works.py`.
  - **File replace-only, no removal**: `PATCH` can swap the PDF, but a work
    can never end up without one (except conference participation, which
    can start with none).
  - **DOI duplicates** are a soft, confirmable warning (not a hard block)
    scoped per employee — two different employees may share a DOI freely.
  - **PDF validation** now includes a real `%PDF-` magic-byte check
    (dependency-free), catching a `.docx` renamed to `.pdf`.
  - Implemented optional enhancements: a **per-category summary** (total
    count) at the top of the dashboard's works section, and a **project-name
    autocomplete** (datalist, sourced from the employee's own prior
    entries).
- **Official annual report module**: every `ScientificWork` record carries a
  derived `report_code` (e.g. `2.1`, `3.4.2`, `6.3`) computed from
  category-specific classification fields, backfilled via
  `python manage.py recalc_report_codes`. Key decisions:
  - **Admin institute-wide report = a JWT-protected `staff`-only endpoint**
    (`/api/reports/institute/`), not a custom Django admin view.
  - **Per-employee breakdown table shows each employee's own
    non-deduplicated counts**; only the top-line institute totals are
    deduplicated (by normalized DOI, falling back to a title+category+year
    signature). Two employees registering the "same" work still both see
    it in their own personal report.
  - **Per-laboratory breakdown**: each deduplicated group is attributed to
    its representative record's department, so department numbers always
    sum exactly to the institute total.
  - **Taxonomy migration never guesses**: where old data has no clean
    equivalent in the new official categories, the record is left
    unclassified (`report_code=""`) and surfaced in the report's warning
    banner — verified against simulated legacy data covering every case.
- **Report drill-down and ZIP export**: every non-zero count (per line, per
  quartile cell, per section "Jami") is clickable in both report views,
  opening a modal listing the exact underlying records — reusing the exact
  same counting function (`resolve_line_records()`) the summary counts use,
  so a modal's row count can never drift from what's shown on the report
  (this equality is asserted directly in tests, not just assumed).
  - The **institute modal shows one deduplicated row per co-authored work**,
    listing every institute co-author (main author marked); the **personal
    modal is never deduplicated** and never shows an author column, since
    every row is already the employee's own.
  - Ownership/staff-only permission checks are enforced at the API layer on
    both the listing and ZIP endpoints, not just hidden in the UI — with
    tests confirming an employee cannot reach another's records and a
    non-staff user is rejected from every institute endpoint.
  - ZIPs are built with **`zipstream-ng`** as a true generator-based stream
    (opens, reads in 64KB chunks, and closes one file at a time) rather
    than buffering the whole archive in memory or on disk, per the request.
    Each ZIP includes a `_haqida.txt` manifest and skips certificate-less
    records with a note.
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

Running `python manage.py migrate` (or `docker compose up -d --build`) applies
every migration in order automatically, including a branch+merge (two
migrations were both generated as children of the same parent -- one adding
Bachelor's/Master's degrees, one adding the scientific-works table -- and a
merge migration reconciles them) and the report-taxonomy sequence
(`0006`→`0008`) that migrates old classification fields into the new
official-report taxonomy, renaming `monograph` → `other_publication` along
the way. **Where old data has no clean equivalent in the new official
categories** (e.g. an old "Sanoat namunasi" patent, or a foreign software
certificate), the record is left unclassified rather than guessed at — it'll
show up in that employee's "Hisobot" warning banner. Both this and the
original documents→works migration were tested against simulated production
data (covering every mapping case) before release.

If you have a very large `ScientificWork` table and want to double-check
everything classified as expected after upgrading, run:

```bash
python manage.py recalc_report_codes
```

This is idempotent and safe to run any time.

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
category filtering) — **88 tests total**, including two dedicated files:

- `specialists/test_reports.py` — `report_code` derivation for every
  category/classification combination, section totals never double-counting
  subset ("jumladan") rows, the 2.1 quartile matrix, DOI-based institute
  dedup (same DOI across employees counts once institute-wide but appears
  in every personal report), per-category year-source selection, the
  conference-participation PDF exception, and report endpoint access
  control (anonymous/non-staff rejected).
- `specialists/test_report_lines.py` — every line/quartile-cell/section-total
  drill-down count exactly matches the report summary (asserted directly,
  not just assumed), ownership isolation on `/reports/me/line/*`, staff-only
  enforcement on `/reports/institute/line/*`, ZIP contents (unique names,
  skips certificate-less records, includes the manifest), one deduplicated
  row per co-authored work in the institute modal, and a 50-record ZIP
  smoke test for the streaming path.

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
| GET | `/me/` | JWT | basic account info, incl. `is_staff` |
| GET/PATCH | `/specialists/me/` | JWT, verified | own profile, photo replace/remove |
| GET/POST | `/specialists/me/works/?category=&page=&ordering=&report_code=` | JWT, verified | list/create own works, no count cap |
| GET/PATCH/DELETE | `/specialists/me/works/{id}/` | JWT, verified | edit (incl. PDF replace) or delete a single work |
| GET | `/reports/me/?year=&date_from=&date_to=` | JWT, verified | structured report: sections, quartile matrix, unclassified list |
| GET | `/reports/me/line/?code=&year=` | JWT, verified | records behind one line/quartile-cell/section-total (own only) |
| GET | `/reports/me/line/zip/?code=&year=` | JWT, verified (10/min) | streamed ZIP of that line's own PDFs |
| GET | `/reports/me/export/?year=` | JWT, verified | Excel download of the personal report |
| GET | `/reports/institute/?year=&department=&employee=` | JWT, **staff only** | deduplicated institute totals + per-lab/per-employee breakdowns |
| GET | `/reports/institute/line/?code=&year=&department=&employee=` | JWT, **staff only** | deduplicated records behind one line, WITH co-author list |
| GET | `/reports/institute/line/zip/?code=&year=&department=` | JWT, **staff only** (10/min) | streamed ZIP, one file per deduplicated work (main author's copy preferred) |
| GET | `/reports/institute/export/?year=&department=` | JWT, **staff only** | Excel download of the institute report |

**`ScientificWork` categories** (`category` field): `foreign_article`,
`local_article`, `thesis`, `conference_participation`, `patent`,
`other_publication`. Required fields differ per category — see
`specialists/serializers.py::ScientificWorkSerializer.CATEGORY_REQUIRED_FIELDS`
(plus the conditional rules for article quartiles and thesis local-conference
level in `validate()`). A PDF file is required on create for every category
**except `conference_participation`**; `PATCH` can replace it but never
remove it. A same-employee DOI duplicate returns `{"code": "duplicate_doi",
...}` (400) unless the request also includes `confirm_duplicate=true`.

Every record carries a derived, indexed `report_code`
(`specialists/report_codes.py::compute_report_code`) mapping it to exactly
one official annual-report line (`2.1`–`6.7`); recomputed on every save, and
backfillable via `python manage.py recalc_report_codes`.

**Line drill-down `code` values** (for `/reports/*/line*` endpoints): a
plain leaf code (`2.1`), the combined local-conference code (`3.4`), a
subset code (`5.2`/`5.4`), a quartile-qualified article code
(`2.1:scopus:Q1`), or a section id for its "Jami" total (`II`..`VI`). The
same `resolve_line_records()` function backs both the count shown on the
report and the modal's row list, so they can never drift apart — this is
asserted directly in `specialists/test_report_lines.py`.

ZIP downloads are built with `zipstream-ng` as a true generator-based
stream (`StreamingHttpResponse`) — files are opened, read in 64KB chunks,
and closed one at a time; nothing is buffered fully in memory or written
to a temp file. Each ZIP includes a `_haqida.txt` manifest listing what was
included and noting any records skipped for having no certificate.

## Future work (per section 10 of the seismology spec, and the change-request documents)

- ORCID / Google Scholar / Scopus links + a general publications list on the profile.
- A "Bo'limlar" browse page listing departments with their staff.
- Language switcher (uz / ru / en) — the `i18n/uz.js` structure is ready for it.
- "DOI orqali to'ldirish" auto-fill on the foreign/local article form via the Crossref API.
- A "Ma'lumotlarni to'ldirish" wizard walking employees through unclassified records one by one.
- Cached institute-wide report results per (year, department), if aggregation gets slow at scale.
- Report snapshots (freeze a submitted year so later edits don't change it).
- PDF export of the report form for signing.

---

## Manual testing checklist

1. Open `http://localhost:5173` — centered hero with the seismogram motif,
   search console (name + department), logo top-left, Kirish/Ro'yxatdan
   o'tish top-right.
2. Search by name and separately by department — results filter correctly
   without logging in; each card shows a total works count.
3. Register a new employee, verify the email code, log in → `/dashboard`.
4. In **"Ilmiy ishlarim"**, add records covering all six categories
   (including at least one Scopus/WoS article with `indexed_in = both`
   and different Scopus/WoS quartiles, one local-conference thesis in
   each of the two sub-levels, one Anjumanda ishtirok **without** a
   certificate, and one monograph published abroad).
5. Try saving a record without a PDF (any category except Anjumanda
   ishtirok) — confirm the error; confirm Anjumanda ishtirok saves fine
   without one, showing "Sertifikat yuklanmagan" in the table.
6. Open **"Hisobot"** — verify every section's lines and totals (5.2
   should NOT inflate the section V total). Every non-zero count,
   including the 2.1 quartile cells and each section's "Jami", should be
   an underlined, clickable button; zero counts stay plain text.
7. Click a count → confirm the drill-down modal lists exactly that many
   records, with no author column, correct metadata for that category,
   and a working per-record download link (or "Sertifikat yo'q" if
   there's no file). Click **"Barchasini ZIP qilib yuklash"** and confirm
   the ZIP opens with the right files plus a `_haqida.txt` manifest.
8. Export to Excel from the dashboard — confirm the file downloads and
   opens with the section headers, numbered lines, and quartile columns.
9. Open that employee's public profile — confirm the six tabs (only
   non-empty ones) and every row's PDF download.
10. As a second employee, register a work with the **same DOI** as the
    first employee's (co-authorship). As an `is_staff` account, open
    **"Institut hisoboti"** — confirm the shared work counts once in the
    institute total (see the "N ta takroriy yozuv birlashtirildi" note),
    click that line's count, and confirm the modal shows **one row with
    both authors listed** (main author marked), and that the ZIP contains
    exactly one file named with the main author's surname.
11. Confirm a non-staff, logged-in account gets redirected away from
    `/admin-report`, gets a 403 from `/api/reports/institute/*`, and
    cannot retrieve or download another employee's records via
    `/api/reports/me/line/*` (only ever sees their own).
12. Visit a nonsense URL like `/foo/bar` → the 404 page.
