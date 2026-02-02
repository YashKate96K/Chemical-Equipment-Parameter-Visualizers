# Chemical Equipment Parameter Visualizer

Interactive web and desktop app to upload chemical equipment datasets, explore them with a dynamic dashboard, and export professional PDF reports.

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
- **Desktop app** (PyQt5) with:
  - Same analytics panels as the web frontend (Summary Stats, Insights, Outliers by Metric).
  - Real-time chart rendering with matplotlib.
  - Clear/Update controls and dataset list with cleaned filenames.
  - Asynchronous analytics fetching from the backend.
- **Generate PDF report** with:
  - Dataset overview (rows, columns).
  - Summary statistics and type distribution.
  - Data‑quality highlights (missing values, duplicates).
  - Strongest correlations and variance/skewness per metric.

Backend: **Django + DRF**  
Frontend: **React 18 + Vite + TailwindCSS + Recharts**  
Desktop: **PyQt5 + matplotlib + numpy + scipy**

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

## 2. Backend (Django API)

### 2.1. Setup and install dependencies

From the project root:

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
# source .venv/bin/activate

pip install -r requirements.txt
```

### 2.2. Migrate database and create admin (optional)

```bash
python manage.py migrate
python manage.py createsuperuser
```

### 2.3. Run backend server

```bash
python manage.py runserver 0.0.0.0:8000
```

Backend base URL (local):

```text
http://localhost:8000/api/
```

### 2.4. Main API endpoints

- `POST /api/upload/` – upload CSV dataset
- `GET  /api/datasets/` – list datasets
- `GET  /api/datasets/<id>/health/` – JSON health + rows for Dynamic Data Explorer
- `GET  /api/datasets/<id>/report/` – generate PDF report
- `GET  /api/datasets/<id>/rows/` – paginated dataset rows for desktop analytics
- `GET  /api/datasets/<id>/quality_metrics/` – quality metrics for desktop analytics
- `POST /api/auth/register/` – register user `{ "username": "...", "password": "..." }`
- `POST /api/auth/token/` – obtain auth token `{ "username": "...", "password": "..." }`

Authentication uses **Django REST Framework TokenAuthentication**.

---

## 3. Desktop App (PyQt5)

### 3.1. Install dependencies

From the project root:

```bash
cd desktop
pip install -r requirements.txt
```

### 3.2. Run desktop app

```bash
python main.py
```

The desktop app connects to the same backend API as the web frontend. Features:

- Dataset list with cleaned, user-friendly filenames.
- Chart controls (type, X/Y axis selectors, Update/Clear buttons).
- Right-side analytics panel with Summary Stats, Insights, and Outliers by Metric.
- Asynchronous analytics fetching (rows + quality metrics) from the backend.

---

## 4. Frontend (React + Vite)

### 4.1. Install dependencies

From the project root:

```bash
cd frontend
npm install
```

### 4.2. Configure environment

Create `.env` in `frontend` (beside `package.json`) based on `.env.example`:

```env
VITE_API_BASE_URL=http://localhost:8000/api
VITE_API_TOKEN=
```

- `VITE_API_BASE_URL` must point to your backend `/api`.
- `VITE_API_TOKEN` can stay empty; it is filled after sign‑in.

### 4.3. Run frontend dev server

```bash
npm run dev
```

Frontend dev URL (default):

```text
http://localhost:5173/
```

---

## 5. Using the Apps Locally

### Web Frontend

1. **Start backend**  
   `python manage.py runserver` (in `backend/`).

2. **Start frontend**  
   `npm run dev` (in `frontend/`).

3. **Open the app**  
   Go to `http://localhost:5173/` in your browser.

4. **Sign up and sign in**
   - Sign up → `POST /api/auth/register/`.
   - Sign in → `POST /api/auth/token/` (returns an auth token used by the frontend).

5. **Upload a dataset (CSV)**
   - Header row is used for column names.
   - Numeric columns are detected automatically (numbers or numeric strings).

6. **Explore a dataset**
   - Open the dataset **Dashboard**.
   - Use **Dynamic Data Explorer** for:
     - Summary Stats (mean, min, max, std, missing)
     - Outliers & "Outliers by Metric"
     - Correlation heatmap
     - Boxplots
     - K‑Means clustering
     - Data table with search and column toggles

7. **Download PDF report**
   - From the dashboard, generate a PDF via `/api/datasets/<id>/report/`.

### Desktop App

1. **Start backend**  
   `python manage.py runserver` (in `backend/`).

2. **Run desktop app**  
   `python main.py` (in `desktop/`).

3. **Select a dataset**  
   - Dataset list shows cleaned, user-friendly filenames.
   - Select a dataset to load it into the visualization widget.

4. **Explore charts and analytics**  
   - Choose chart type and axes.
   - Click **Update** to render the chart.
   - View the right-side analytics panel (Summary Stats, Insights, Outliers by Metric) computed from real dataset rows.
   - Use **Clear** to reset the chart.

5. **Export chart**  
   - Use the Export button to save the current chart as PNG/PDF/SVG.

---

## 6. Deployment

This project is designed for:

- **Backend** → Render
- **Frontend** → Netlify

### 6.1. Backend on Render

1. Create a new **Web Service** on Render pointing to the `backend` folder.
2. Environment variables (minimum):

   - `DJANGO_SECRET_KEY=<your-secret>`
   - `DEBUG=False`
   - Database configuration (if not using default SQLite).

3. Build & Start commands:

   - Build: `pip install -r requirements.txt && python manage.py migrate`
   - Start: `gunicorn config.wsgi:application --bind 0.0.0.0:8000`

4. Note the public URL, e.g.:

   ```text
   https://chemical-equipment-parameter-visualizer-XXXX.onrender.com
   ```

### 6.2. Frontend on Netlify

1. In `frontend/.env` (for production), set:

   ```env
   VITE_API_BASE_URL=https://<your-backend>.onrender.com/api
   VITE_API_TOKEN=
   ```

2. Netlify configuration:

   - Build command: `npm run build`
   - Publish directory: `dist`

3. **SPA routing fix (important)**

   For React Router to work on reload, ensure this file exists:

   `frontend/public/_redirects`

   ```text
   /*    /index.html   200
   ```

   This makes refresh on `/dashboard/...` or `/signup` work correctly on Netlify.

---

## 7. Common Issues & Fixes

- **Netlify 404 “Page not found” on reload**  
  `_redirects` missing or not deployed. Ensure `frontend/public/_redirects` contains:

  ```text
  /*    /index.html   200
  ```

- **Sign in failed**  
  Usually means either:
  - Username/password are wrong for the current backend DB, or
  - The frontend `VITE_API_BASE_URL` does not match the backend you’re using.

- **Invalid token**  
  Tokens are DRF auth tokens stored in the DB. If the DB is reset or changed, old tokens become invalid. Simply sign in again to obtain a new token.

- **Dynamic Explorer shows blank stats / bounds [0.00, 0.00]**  
  Ensure numeric fields are numeric or numeric strings (e.g. `120` or `"120"`), not values with units like `"120 kg"`.

---

## 8. Script Cheat Sheet

**Backend**

```bash
docker compose up --build
```

- Backend: http://localhost:8000  
- Frontend: http://localhost:5173

---

## 9. Notes

- Only the **last 5 datasets** are kept; older ones are pruned on upload.
- Token auth is used for protecting upload and dataset endpoints.
- Frontend and backend URLs are configurable via `.env` files.
- Desktop app fetches analytics data from the same backend API as the web frontend.
- Desktop analytics panel shows all numeric columns (scrollable) and updates automatically on dataset selection.
