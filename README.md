# Chemical Equipment Parameter Visualizer

Interactive web and desktop application for uploading, exploring, and analyzing chemical equipment datasets with advanced visualizations and PDF reporting capabilities.

---

## 🚀 Features Overview

### 📊 **Data Analysis & Visualization**
- **Upload CSV/XLSX** datasets with automatic column type detection
- **Multiple Chart Types**: Line, Bar, Scatter, Histogram, Box Plot, Heatmap, Donut Chart
- **Advanced Analytics**: Correlation analysis, outlier detection, statistical summaries
- **Smart Insights**: Automated observations about data patterns and anomalies

### 🖥️ **Desktop Application (PyQt5)**
- **Native Desktop Experience** with modern UI design
- **Interactive Charts**: Real-time matplotlib rendering with multiple chart types
- **Analytics Panel**: Summary Stats, Insights, and Outliers by Metric
- **PDF Report Generation**: Comprehensive reports with charts and analysis
- **Asynchronous Data Loading**: Non-blocking analytics fetching from backend

### 🌐 **Web Frontend (React)**
- **Modern React Dashboard** with Vite and TailwindCSS
- **Dynamic Data Explorer**: Interactive table with search and pagination
- **Responsive Design**: Works on desktop and mobile devices
- **Authentication System**: Token-based user authentication

### 📋 **Backend API (Django)**
- **RESTful API**: Full CRUD operations for datasets
- **Data Processing**: Automatic validation and quality metrics
- **PDF Generation**: Server-side report creation with ReportLab
- **Authentication**: Token-based security with Django REST Framework

---

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Desktop App   │    │   Web Frontend  │    │   Backend API   │
│   (PyQt5)       │◄──►│   (React)       │◄──►│   (Django)      │
│                 │    │                 │    │                 │
│ • Matplotlib    │    │ • Recharts      │    │ • DRF           │
│ • PDF Reports   │    │ • TailwindCSS   │    │ • ReportLab     │
│ • Analytics     │    │ • Router        │    │ • PostgreSQL    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

---

## 📋 Expected CSV Structure

### Minimal Example:
```csv
Equipment Name,Type,Flowrate,Pressure,Temperature
Pump-1,Pump,120,5.2,110
Compressor-1,Compressor,95,8.4,95
Valve-1,Valve,60,4.1,105
```

### Supported Features:
- ✅ **Automatic column detection** (numeric vs categorical)
- ✅ **Flexible naming** - any column names supported
- ✅ **Mixed data types** - handles various formats
- ✅ **Missing values** - robust handling of incomplete data

---

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8+ 
- Node.js 16+
- Git

### 1. Backend Setup

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate
# macOS/Linux  
# source venv/bin/activate

pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser  # Optional
```

### 2. Desktop App Setup

```bash
cd desktop
pip install -r requirements.txt
```

### 3. Frontend Setup

```bash
cd frontend
npm install
```

---

## 🚀 Running the Applications

### Backend Server
```bash
cd backend
python manage.py runserver 0.0.0.0:8000
```
**API Base URL**: `http://localhost:8000/api/`

### Desktop Application
```bash
cd desktop
python main.py
```

### Web Frontend
```bash
cd frontend
npm run dev
```
**Frontend URL**: `http://localhost:5173/`

---

## 📊 Using the Applications

### Desktop Application Workflow

1. **Start Backend**: Run Django server first
2. **Launch Desktop App**: `python main.py`
3. **Load Dataset**: Select from dataset list
4. **Explore Charts**: 
   - Choose chart type (Line, Bar, Scatter, Histogram, Box, Heatmap, Donut)
   - Select X/Y axes for applicable charts
   - Click "Update" to render
5. **View Analytics**: 
   - Summary Statistics (mean, median, std, min, max)
   - Auto-generated Insights
   - Outlier Detection by column
6. **Generate Reports**: 
   - Click "Generate Report" for comprehensive PDF
   - Use "Export" to save individual charts

### Web Frontend Workflow

1. **Authentication**: Sign up / Sign in
2. **Upload Dataset**: CSV/XLSX file upload
3. **Explore Dashboard**: 
   - Dynamic Data Explorer with interactive charts
   - Real-time statistics and insights
   - Searchable data table
4. **Generate Reports**: Download PDF reports

---

## 🔧 Configuration

### Environment Variables

#### Backend (.env)
```env
DJANGO_SECRET_KEY=your-secret-key
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
```

#### Frontend (.env)
```env
VITE_API_BASE_URL=http://localhost:8000/api
VITE_API_TOKEN=
```

#### Desktop App (.env)
```env
API_BASE_URL=http://localhost:8000/api/
API_TOKEN=your-auth-token
```

---

## 📈 Chart Types & Features

### 📊 **Available Charts**

| Chart Type | Use Case | Data Requirements |
|------------|----------|-------------------|
| **Line Chart** | Trends over time/sequence | 2+ numeric columns |
| **Bar Chart** | Category comparisons | 1 numeric column |
| **Scatter Plot** | Correlation analysis | 2+ numeric columns |
| **Histogram** | Distribution analysis | 1 numeric column |
| **Box Plot** | Statistical summary | 1 numeric column |
| **Heatmap** | Correlation matrix | 2+ numeric columns |
| **Donut Chart** | Categorical distribution | 1 categorical column |

### 🔍 **Analytics Features**

- **Summary Statistics**: Mean, median, std dev, min, max, quartiles
- **Outlier Detection**: IQR-based outlier identification
- **Correlation Analysis**: Pearson correlation matrix
- **Data Quality**: Missing value analysis, data type validation
- **Auto-Insights**: Automated observations about patterns

---

## 📋 API Endpoints

### Authentication
- `POST /api/auth/register/` - User registration
- `POST /api/auth/token/` - Get authentication token

### Datasets
- `POST /api/datasets/` - Upload new dataset
- `GET /api/datasets/` - List all datasets
- `GET /api/datasets/{id}/` - Get dataset details
- `DELETE /api/datasets/{id}/` - Delete dataset

### Analytics
- `GET /api/datasets/{id}/health/` - Dataset health metrics
- `GET /api/datasets/{id}/rows/` - Paginated data rows
- `GET /api/datasets/{id}/quality_metrics/` - Data quality analysis
- `GET /api/datasets/{id}/report/` - Generate PDF report

---

## 🔥 Recent Updates & Features

### ✨ **New Features**
- **Enhanced Heatmap**: Robust correlation matrix with error handling
- **PDF Reports**: Comprehensive reports with charts and analytics
- **Improved Analytics**: Better outlier detection and insights
- **Modern UI**: Updated desktop app with better styling
- **Error Handling**: Comprehensive error messages and debugging

### 🐛 **Bug Fixes**
- Fixed heatmap rendering issues with invalid data
- Improved correlation matrix calculation
- Better handling of missing/invalid data points
- Enhanced error reporting and debugging

### 🎨 **UI Improvements**
- Compact analytics panel design
- Better chart styling and colors
- Improved font sizes and readability
- Modern button and control styling

---

## 🚀 Deployment

### Backend (Render/Heroku)
```bash
# Build command
pip install -r requirements.txt && python manage.py migrate

# Start command  
gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
```

### Frontend (Netlify/Vercel)
```bash
# Build command
npm run build

# Publish directory
dist
```

**Important**: Ensure `frontend/public/_redirects` contains:
```
/*    /index.html   200
```

---

## 🛠️ Development

### Project Structure
```
chemical-equipment-parameter-visualizer/
├── backend/                 # Django REST API
│   ├── visualizer/         # Main app
│   ├── config/            # Django settings
│   └── requirements.txt    # Python dependencies
├── desktop/                # PyQt5 Desktop App
│   ├── app/               # Main application
│   └── requirements.txt   # Python dependencies
├── frontend/              # React Web App
│   ├── src/              # React components
│   └── package.json      # Node dependencies
└── README.md              # This file
```

### Key Technologies

#### Backend
- **Django** - Web framework
- **Django REST Framework** - API framework
- **ReportLab** - PDF generation
- **NumPy/SciPy** - Data processing
- **PostgreSQL** - Database (production)

#### Desktop
- **PyQt5** - GUI framework
- **Matplotlib** - Charting library
- **NumPy/SciPy** - Data processing
- **Requests** - HTTP client

#### Frontend
- **React 18** - UI framework
- **Vite** - Build tool
- **TailwindCSS** - CSS framework
- **Recharts** - Charting library
- **Axios** - HTTP client

## 📝 License & Contributing

### License
This project is licensed under the MIT License - see the LICENSE file for details.


---

---

## 📊 Quick Start Summary

```bash
# 1. Clone and setup
git clone <repository-url>
cd chemical-equipment-parameter-visualizer

# 2. Backend
cd backend
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

# 3. Desktop (new terminal)
cd desktop
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
# 4. Frontend (new terminal)
cd frontend
npm install && npm run dev
```

**Access Points:**
- 🌐 **Web App**: http://localhost:5173
- 🖥️ **Desktop App**: Native application window
- 🔌 **Backend API**: http://localhost:8000/api

---

