# FormVerse

A full-stack **multi-page** web app — Flask serves both the pages and the API, so there's
one server, one URL, and real browser navigation (every sidebar link and button is an actual
page load with its own URL, not a JS view-toggle). SQLite (Python's built-in `sqlite3`) is
the database — no separate database server to install.

This replaces the earlier single-file HTML prototype: the frontend and backend are now one
app, which also removes the "do these need to be in the same folder / running together"
confusion — there's only one thing to run.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Seed demo data (recommended)

```bash
python seed.py
```

Creates a demo account with sample forms and responses already in place:

```
Email:    demo@formverse.io
Password: password123
```

## Run it

```bash
python run.py
```

Open **http://127.0.0.1:5000** in your browser. That's it — one process, one port, pages and
API both served from there.

## What changed from the single-file version

- **Real multi-page navigation.** `/`, `/login`, `/signup`, `/app/dashboard`, `/app/forms`,
  `/app/builder`, `/app/builder/<id>`, `/app/responses`, `/app/analytics`, `/app/settings` are
  all distinct server-rendered routes with their own URLs — back/forward and bookmarking work
  as expected, and login/signup are plain HTML forms (no JS required for auth to work).
- **Session-cookie auth** for the browser (set at login/signup), so page loads and the
  dynamic `fetch()` calls inside each page authenticate automatically — no manual token
  handling in the frontend anymore. A JWT `Authorization: Bearer` header still works too, for
  external API clients (curl, Postman, a future mobile app).
- **Share link + QR code.** Publishing a form (or clicking "Share" on any published form in
  My Forms) opens a modal with the shareable link, a copy button, a QR code, a downloadable
  QR image, and an embed `<iframe>` snippet. The QR image comes from the free
  `api.qrserver.com` image API — no API key needed, but it does mean generating a QR code
  requires the visitor's browser to have internet access. Swap in a client-side QR library
  (e.g. `qrcode.js`) under `static/js/` if you'd rather have zero external dependency.
- **A real public form page.** The share link now goes somewhere — `/f/<slug>` renders the
  published form for respondents (all 18 field types), validates required fields, and submits
  real responses into the same database your dashboard reads from. No login needed to view or
  fill it out.
- **Real dark mode.** The Settings toggle now actually switches a full dark color palette
  (not just a cosmetic switch flip) and persists across page loads and navigation via
  `localStorage`, with a small inline script in every page's `<head>` that applies it before
  first paint (no flash of light mode).
- **Bug fixes**: choice fields (dropdown/checkbox/radio/multiple-choice) now have a working
  options editor in the builder inspector — previously their choices were hardcoded to "Option
  A/B/C" with no way to edit them. The responses search box is now wired up. Buttons show a
  loading/disabled state during save so you can't double-submit.
- **Smoother feel**: a slim top progress bar during API calls, toast notifications instead of
  jarring `alert()` popups for routine confirmations (destructive actions like delete still
  use a native confirm dialog on purpose), skeleton loading states instead of blank tables,
  and a subtle fade-in on page load.
- **Shared CSS/JS** moved into `app/static/` instead of one giant inline `<script>` — each
  page loads only the JS it needs (`dashboard.js`, `builder.js`, etc.), plus a shared `api.js`
  for the fetch/toast/progress-bar/theme/share-modal helpers.

## Project layout

```
app/
  templates/       Jinja2 page templates (one per route)
  static/css/      shared stylesheet
  static/js/       api.js (shared) + one file per page
  pages/           page_routes.py — server-rendered routes (/, /login, /app/*, ...)
  routes/          JSON API blueprints (/api/*)
  auth_service.py  shared register/login logic used by both page forms and the JSON API
  auth_utils.py    JWT + session helpers, @token_required / @page_login_required decorators
  db.py            schema + sqlite connection helper
run.py             entry point
seed.py            demo data
```

## API overview (still available at `/api/*`)

| Area | Endpoints |
|---|---|
| Auth | `POST /api/auth/register`, `/login`, `/logout`, `/forgot-password`, `/reset-password`, `/change-password`, `GET/PATCH/DELETE /api/auth/me` |
| Forms | `GET/POST /api/forms`, `GET/PUT/DELETE /api/forms/<id>`, `POST /api/forms/<id>/duplicate`, `/publish`, `/archive` |
| Public (respondents) | `GET /api/public/forms/<shareSlug>`, `POST /api/public/forms/<shareSlug>/submit` |
| Responses | `GET /api/forms/<id>/responses`, `GET/DELETE /api/responses/<id>`, `POST /api/forms/<id>/responses/bulk-delete`, `GET /api/forms/<id>/responses/export` |
| Analytics | `GET /api/forms/<id>/analytics`, `GET /api/dashboard/summary` |
| Notifications | `GET /api/notifications`, `POST /api/notifications/<id>/read` |
| Admin (role=admin) | `GET /api/admin/users`, `PATCH /api/admin/users/<id>`, `GET /api/admin/forms`, `GET /api/admin/stats` |

## What's real vs. stubbed

- **Real**: hashed-password auth (Werkzeug), session + JWT auth, all form/field CRUD, response
  storage/retrieval, CSV export, analytics aggregated from actual database rows, admin panel
  with real data, drag-and-drop builder with a working options editor for choice fields.
- **Stubbed** (noted in-code where relevant):
  - **Email delivery** — password reset shows the token directly on the confirmation page
    instead of emailing it (no provider like SendGrid/SES configured).
  - **Excel (.xlsx) export** — falls back to CSV; add `openpyxl` for real `.xlsx`.
  - **File uploads / Cloudinary** — the `file` field type is selectable on the public form
    page, but files aren't actually persisted anywhere yet (only the filename is recorded) —
    wire up Cloudinary's Python SDK and an `/api/uploads` route to complete this.
  - **Payments (Stripe/Razorpay)** — not implemented.

## Production notes

- Swap the dev server (`python run.py`) for `gunicorn`/`waitress` before deploying.
- Set a real `FORMVERSE_SECRET_KEY` environment variable — don't use the default.
- For multi-instance production, migrating SQLite to Postgres means adding `psycopg2` and
  swapping the raw-SQL layer in `app/db.py` — the schema and query shapes translate directly.
