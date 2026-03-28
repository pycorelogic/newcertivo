# Certivo Blog - Vercel Deployment Checklist

Use this checklist for a Vercel-compatible deployment of the current Flask app.

---

## Code Changes Already Applied

- [x] Added a Vercel serverless entrypoint at `api/index.py`
- [x] Added `vercel.json` with a Python function build and a catch-all route
- [x] Switched Vercel logging to stdout instead of rotating log files on disk
- [x] Disabled runtime SCSS compilation on Vercel by default
- [x] Normalized `DATABASE_URL` so `postgres://` also works
- [x] Auto-derived `SITE_URL` from `VERCEL_URL` when `SITE_URL` is not set
- [x] Disabled uploads on Vercel by default to avoid broken ephemeral file storage

---

## Required Before Deploy

### Database
- [ ] Use PostgreSQL or another external SQL database
- [ ] Set `DATABASE_URL` in the Vercel dashboard
- [ ] Confirm the database is reachable from Vercel functions
- [ ] Do not rely on local SQLite in production

### App Secrets
- [ ] Set `FLASK_ENV=production`
- [ ] Set `SECRET_KEY` to a strong random value
- [ ] Set `MAIL_USERNAME` and `MAIL_PASSWORD` if contact emails should work
- [ ] Set `ADMIN_EMAIL`

### Site Metadata
- [ ] Set `SITE_URL` if you do not want to rely on the auto-detected Vercel URL
- [ ] Set `SITE_NAME`, `SITE_TAGLINE`, and analytics/ad settings as needed

---

## Vercel-Specific Decisions

### Uploads
- [ ] Keep `UPLOADS_ENABLED=false` on Vercel unless you add persistent object storage
- [ ] If uploads are required, move media storage to an external service such as Vercel Blob, S3, or Cloudinary
- [ ] Do not depend on `app/static/uploads` for user-generated files in production

### Logging
- [ ] Keep stdout logging enabled on Vercel
- [ ] Do not expect `logs/` files to persist between executions

### Assets
- [ ] Let Vercel run `python compile_scss.py` during the build
- [ ] Confirm `/static/...` assets load correctly after deployment

---

## Recommended Environment Variables

```bash
FLASK_ENV=production
FLASK_DEBUG=0
SECRET_KEY=<strong-random-secret>
DATABASE_URL=<postgresql-connection-string>
SITE_URL=https://your-domain.com
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=<smtp-username>
MAIL_PASSWORD=<smtp-password>
ADMIN_EMAIL=admin@your-domain.com
LOG_TO_STDOUT=true
UPLOADS_ENABLED=false
COMPILE_SCSS_ON_BOOT=false
```

---

## Deploy Steps

1. Import the project into Vercel.
2. Set the environment variables in the Vercel dashboard.
3. Deploy once to confirm the app boots and static files resolve.
4. Visit `/health` to confirm database connectivity.
5. Test homepage, blog pages, admin login, contact form, and any email flow.

---

## Known Constraints On Vercel

- SQLite is not suitable for production Vercel deployments.
- Local file uploads are not persistent on Vercel serverless functions.
- File-based rotating logs are not suitable for Vercel.
- Any background job or long-running process should be moved outside the request lifecycle.

---

## Nice Next Improvements

- [ ] Replace local uploads with Vercel Blob or another object store
- [ ] Add a dedicated database migration workflow
- [ ] Add deployment verification for `/health`, `/`, and `/static/css/main.css`
- [ ] Add a short Vercel deploy guide to project docs if this becomes the primary platform

---

Last updated: March 28, 2026
