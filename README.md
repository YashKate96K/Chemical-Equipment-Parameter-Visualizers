# Chemical Equipment Parameter Visualizer

A full-stack app to upload chemical equipment CSVs, compute stats, visualize charts, and generate PDF reports.

## Features
- Backend (Django + DRF) with CSV upload, validation, stats, preview, last-5 retention, PDF reports.
- Frontend (React + Vite + Tailwind + Chart.js) to upload, visualize, and download reports.
- Desktop Client (PyQt5) to upload, view summary, charts, and download reports.
- Token authentication supported for API clients.
- Docker setup and GitHub Actions CI.

## CSV Format
```
Equipment Name,Type,Flowrate,Pressure,Temperature
Pump-1,Pump,120,5.2,110
Compressor-1,Compressor,95,8.4,95
Valve-1,Valve,60,4.1,105
```

## Backend
- Python 3.11+, Django 4+, DRF 3.14+
- Endpoints:
  - POST `/api/upload/` — body: multipart with `file` CSV
  - GET `/api/datasets/` — last 5 datasets
  - GET `/api/datasets/<id>/report/` — PDF report
  - (optional) POST `/api/auth/token/` — obtain token with username/password

### Run locally
```
python -m venv .venv && .venv/Scripts/activate  # Windows
pip install -r backend/requirements.txt
python backend/manage.py migrate
python backend/manage.py createsuperuser  # optional for token
python backend/manage.py runserver
```

## Frontend
- React 18, Vite, Tailwind, Chart.js

### Setup
```
cd frontend
npm install
cp .env.example .env  # set VITE_API_BASE_URL
npm run dev
```

## Desktop Client
```
cd desktop
pip install -r requirements.txt
set DESKTOP_API_BASE_URL=http://localhost:8000/api
python main.py
```

## Docker
```
docker compose up --build
```
- Backend: http://localhost:8000
- Frontend: http://localhost:5173

## CI
- Backend: installs, migrates, basic check.
- Frontend: installs, builds.

## Notes
- Keep only last 5 datasets; older are deleted on upload.
- PDF is generated with ReportLab.
- Set token in frontend `.env` via `VITE_API_TOKEN` and in desktop `.env` via `DESKTOP_API_TOKEN` if required.
