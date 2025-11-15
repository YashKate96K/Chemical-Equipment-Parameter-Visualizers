# Deploy Guide

This project is a monorepo with:
- backend/ (Django API)
- frontend/ (Vite + React)

## Option A: One-click with Render Blueprint (backend) + Netlify (frontend)

1) Backend API on Render
- Click "New +" → "Blueprint" and select this repository.
- Render will detect `render.yaml` in repo root and create `chemical-visualizer-api` service.
- Confirm settings, then click "Apply" to deploy.

2) Frontend on Netlify
- Install Netlify CLI (Windows):
  - `npm.cmd install -g netlify-cli`
  - `netlify login`
- Initialize site from `frontend/`:
  - `cd frontend`
  - `netlify init --manual` (choose Create & configure a new site)
- Set API base URL (after backend is live):
  - `netlify env:set VITE_API_BASE_URL https://YOUR_RENDER_HOST.onrender.com/api`
- Deploy:
  - `netlify deploy --build --prod`

3) Update backend CORS/CSRF on Render
- In the Render service → Environment, set:
  - `CORS_ALLOWED_ORIGINS=https://YOUR_NETLIFY_SITE.netlify.app`
  - `CSRF_TRUSTED_ORIGINS=https://YOUR_NETLIFY_SITE.netlify.app`

## Option B: Manual (Render Web Service)
- Root Directory: `backend`
- Build Command:
  - `pip install -r requirements.txt && python manage.py migrate`
- Start Command:
  - `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT`
- Environment:
  - `DEBUG=False`
  - `SECRET_KEY=<strong-secret>`
  - `ALLOWED_HOSTS=${RENDER_EXTERNAL_HOSTNAME}`
  - `CORS_ALLOWED_ORIGINS=https://YOUR_NETLIFY_SITE.netlify.app`
  - `CSRF_TRUSTED_ORIGINS=https://YOUR_NETLIFY_SITE.netlify.app`

## Verify
- Open Netlify site → upload CSV/XLSX → Quick Summary shows.
- Use “Open Dashboard →” or dataset “Dashboard” → charts load.
- Try PDF download.

## Troubleshooting
- CORS/CSRF errors: Ensure the Netlify domain is present in both `CORS_ALLOWED_ORIGINS` and `CSRF_TRUSTED_ORIGINS` on Render.
- 404 on API: Confirm VITE_API_BASE_URL in Netlify env points to the Render API.
- Port conflicts locally: Run Django on a different port and update `.env` in frontend.
