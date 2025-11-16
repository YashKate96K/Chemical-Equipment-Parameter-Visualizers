# Chemical Equipment Parameter Visualizer

Interactive web app to upload chemical equipment datasets, explore them with a dynamic dashboard, and export professional PDF reports.

---

## What this app does

- **Upload CSV / XLSX** datasets of equipment parameters.
- **Authenticate** with Sign Up / Sign In (token-based auth via Django REST Framework).
- **Explore data** in a dynamic React dashboard:
  - Automatic detection of numeric & categorical columns.
  - Summary cards with mean/median/min/max/std and missing-value counts.
  - Correlation heatmap, boxplots, category distributions, K‑Means clustering.
  - AI‑style insights (variability, skewness, correlations, outliers, dominant categories).
  - Outliers overview per metric and a searchable, paginated data table.
- **Generate PDF report** with:
  - Dataset overview (rows, columns).
  - Summary statistics and type distribution.
  - Data‑quality highlights (missing values, duplicates).
  - Strongest correlations and variance/skewness per metric.

Backend: **Django + DRF**  
Frontend: **React 18 + Vite + TailwindCSS + Recharts**

---

## Expected CSV structure (minimal example)

```text
Equipment Name,Type,Flowrate,Pressure,Temperature
Pump-1,Pump,120,5.2,110
Compressor-1,Compressor,95,8.4,95
Valve-1,Valve,60,4.1,105
```

Additional columns are allowed; the dashboard adapts automatically.

---

## Backend (API server)

### Tech

- Python 3.11+
- Django 4+
- Django REST Framework 3.14+

### Key endpoints (prefixed with `/api/`)

- `POST /api/upload/`  
  Upload a CSV/XLSX file as `file`. Validates, computes summary stats, and stores a preview.

- `GET /api/datasets/`  
  List the latest datasets (limited to last 5 by design).

- `GET /api/datasets/<id>/health/`  
  Returns rows and analytics used by the React dashboard.

- `GET /api/datasets/<id>/report/`  
  Generates the PDF report described above.

- `POST /api/auth/token/` *(built‑in DRF token view)*  
  Obtain auth token with username/password.

### Run backend locally (Windows example)

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r backend/requirements.txt
python backend/manage.py migrate
python backend/manage.py createsuperuser   # for login
python backend/manage.py runserver        # API at http://localhost:8000/api/
```

---

## Frontend (React dashboard)

### Tech

- React 18
- Vite
- TailwindCSS
- Recharts

### Setup & run

```bash
cd frontend
npm install
cp .env.example .env    # set VITE_API_BASE_URL, e.g. http://localhost:8000/api
npm run dev             # app at http://localhost:5173
```

### Auth & navigation

- On first visit you see **Sign In / Sign Up**.
- After logging in, an auth token is stored and you see:
  - **Home** page: upload datasets, see quick summary and dataset list.
  - **Dashboard** page: full Dynamic Explorer for a selected dataset.
- Sign Out clears token and sends you back to Sign In.

---

## PDF Report

- Generated with **ReportLab** on the backend.
- Styled header with title, filename, and timestamp.
- Two‑column layout with sections for overview, stats, quality, correlations, and variance/skewness.

Download via the frontend action that calls:

```http
GET /api/datasets/<id>/report/
```

---

## Docker (optional)

```bash
docker compose up --build
```

- Backend: http://localhost:8000  
- Frontend: http://localhost:5173

---

## Notes

- Only the **last 5 datasets** are kept; older ones are pruned on upload.
- Token auth is used for protecting upload and dataset endpoints.
- Frontend and backend URLs are configurable via `.env` files.
