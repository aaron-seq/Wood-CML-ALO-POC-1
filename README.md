# Wood AI CML Optimization - Machine Learning Model - prototype 1

![Python](https://img.shields.io/badge/Python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)
![Docker](https://img.shields.io/badge/Docker-Enabled-blue)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 🎯 Project Overview

Advanced Machine Learning system for **Condition Monitoring Location (CML) Optimization** in industrial facilities. This project uses ML algorithms to analyze corrosion data, prioritize inspections, and recommend CML eliminations based on risk assessment and data-driven insights.

### Key Features

- 🤖 **ML-Powered CML Elimination Recommendations** - XGBoost/LightGBM models for intelligent prioritization
- 📊 **Interactive Dashboard** - Real-time visualization of CML status, risk levels, and trends
- 📈 **Time-Series Forecasting** - Predict remaining asset life using Prophet/ARIMA
- 🔍 **Explainable AI** - SHAP values and feature importance for transparent decisions
- 👨‍🔧 **SME Override System** - Engineer validation and model retraining pipeline
- 📄 **Automated PDF Reports** - Client-ready inspection reports with recommendations
- 🐳 **Docker-First Deployment** - Containerized for consistent local/cloud deployment
- 📤 **Excel Upload Interface** - Simple data ingestion via standardized templates

## 🏗️ Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Excel/CSV     │────▶│   FastAPI        │────▶│   PostgreSQL    │
│   Upload        │     │   Backend        │     │   Database      │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   ML Pipeline        │
                    │  - Preprocessing     │
                    │  - Feature Eng.      │
                    │  - XGBoost Model     │
                    │  - Forecasting       │
                    │  - SHAP Explainer    │
                    └──────────────────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   Interactive UI     │
                    │  - Plotly Dashboard  │
                    │  - Data Tables       │
                    │  - PDF Export        │
                    └──────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Git
- 4GB RAM minimum

### Installation

```bash
# Clone the repository
git clone https://github.com/aaron-seq/Wood-AI-CML-ALO-Machine-Learning-Model.git
cd Wood-AI-CML-ALO-Machine-Learning-Model

# Create environment file
cp .env.example .env

# Build and start containers
docker-compose up --build
```

### Access the Application

- **API Documentation**: http://localhost:8000/docs
- **Dashboard**: http://localhost:8000/ (FastAPI serves frontend)
- **Health Check**: http://localhost:8000/health

## 📁 Project Structure

```
Wood-AI-CML-ALO-Machine-Learning-Model/
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI application entry
│   │   ├── api/
│   │   │   ├── routes_cml.py          # CML CRUD endpoints
│   │   │   ├── routes_forecast.py     # Time-series forecasting
│   │   │   ├── routes_report.py       # PDF report generation
│   │   │   └── routes_dashboard.py    # Dashboard data endpoints
│   │   ├── core/
│   │   │   ├── config.py              # Configuration management
│   │   │   └── database.py            # Database connection
│   │   ├── models/
│   │   │   ├── db_models.py           # SQLAlchemy ORM models
│   │   │   └── schemas.py             # Pydantic schemas
│   │   ├── ml/
│   │   │   ├── preprocess.py          # Data preprocessing pipeline
│   │   │   ├── model_elimination.py   # CML elimination model
│   │   │   ├── model_forecast.py      # Time-series forecasting
│   │   │   ├── explainability.py      # SHAP/feature importance
│   │   │   └── model_trainer.py       # Training orchestration
│   │   └── services/
│   │       ├── cml_service.py         # Business logic
│   │       ├── validation_service.py  # Data validation
│   │       └── report_service.py      # PDF generation
│   ├── tests/
│   │   ├── test_api.py
│   │   ├── test_ml.py
│   │   └── test_services.py
│   ├── Dockerfile
│   └── requirements.txt
├── data/
│   ├── raw/
│   │   └── CML_Optimization_Sample_Data.xlsx  # Sample dataset
│   ├── processed/
│   └── models/                        # Saved ML models
├── notebooks/
│   ├── 01_data_exploration.ipynb
│   ├── 02_feature_engineering.ipynb
│   └── 03_model_training.ipynb
├── scripts/
│   ├── fetch_external_data.py         # Download public datasets
│   ├── train_models.py                # Training pipeline
│   └── seed_database.py               # Database initialization
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

## 🧪 Sample Data

The project includes synthetic CML data (`data/raw/CML_Optimization_Sample_Data.xlsx`) with:

- **225 CMLs** across 3 facilities
- **10+ years** of inspection history
- **44 elimination candidates** (low-risk, redundant coverage)
- **12 CMLs** requiring engineering review
- Multiple commodities: Water, Oil, Gas, Steam, etc.
- Various materials: Carbon Steel, Stainless Steel, Chrome Moly, etc.

### Data Schema

| Field | Type | Description |
|-------|------|-------------|
| `CML_ID` | String | Unique CML identifier |
| `Commodity` | String | Fluid/gas type |
| `Material_Type` | String | Pipe material |
| `Feature_Type` | String | Elbow, Tee, Straight, etc. |
| `Average_Corrosion_Rate_mm_per_year` | Float | Historical corrosion rate |
| `Remaining_Life_Years` | Float | Estimated remaining life |
| `Risk_Level` | Enum | Critical/High/Medium/Low |
| `Elimination_Candidate` | Boolean | ML recommendation flag |

## 🔧 API Endpoints

### Health Check
```bash
GET /health
```

### Upload CML Data
```bash
POST /api/v1/cml/upload
Content-Type: multipart/form-data

file: CML_data.xlsx
```

### Get CML Summary
```bash
GET /api/v1/cml/summary
```

### Run ML Inference
```bash
POST /api/v1/cml/analyze
Content-Type: application/json

{
  "facility": "Facility A",
  "threshold": 0.7
}
```

### Forecast CML Thickness
```bash
GET /api/v1/forecast/{cml_id}?periods=24
```

### Export PDF Report
```bash
GET /api/v1/report/generate?facility=Facility A
```

## 🤖 Machine Learning Pipeline

### 1. Data Preprocessing

- Missing value imputation (median for numerics, mode for categories)
- Outlier detection and capping
- Feature engineering:
  - Time-based features (years in service, inspection frequency)
  - Corrosion rate statistics (mean, std, trend)
  - Material-commodity interaction features

### 2. Model Training

**Elimination Model (XGBoost Classifier)**

- Input features:
  - Commodity, Material, Feature Type (one-hot encoded)
  - Avg corrosion rate, Remaining life, Risk level
  - Inspection count, Data quality score
- Target: `Elimination_Candidate` (0/1)
- Metrics: Precision, Recall, F1-Score, AUC-ROC

**Forecasting Model (Prophet/ARIMA)**

- Per-CML time-series modeling
- Inputs: Historical thickness measurements + dates
- Outputs: Future thickness predictions + confidence intervals

### 3. Explainability

- SHAP (SHapley Additive exPlanations) values per prediction
- Global feature importance
- Per-CML explanation reports

## 📊 Dashboard Features

- **Overview Tab**: Total CMLs, eliminations, risk distribution
- **CML Table**: Sortable/filterable table with all CML details
- **Risk Matrix**: Heatmap of risk vs remaining life
- **Elimination Candidates**: List with justification and SHAP values
- **Forecasting View**: Interactive time-series charts
- **SME Override Interface**: Approve/reject recommendations

## 🧪 Testing

```bash
# Run all tests
docker-compose exec app pytest

# Run with coverage
docker-compose exec app pytest --cov=app --cov-report=html

# Run specific test file
docker-compose exec app pytest tests/test_ml.py -v
```

## 📈 Training New Models

```bash
# Inside container
docker-compose exec app python scripts/train_models.py

# Or locally
python scripts/train_models.py --data data/raw/CML_Optimization_Sample_Data.xlsx --output data/models/
```

## 🔐 Environment Variables

```env
# Database
POSTGRES_HOST=db
POSTGRES_PORT=5432
POSTGRES_DB=cml_optimization
POSTGRES_USER=cml_user
POSTGRES_PASSWORD=your_secure_password

# Application
APP_ENV=development
API_VERSION=v1
DEBUG=True

# ML Model
MODEL_PATH=data/models/cml_elimination_model.pkl
MIN_TRAINING_SAMPLES=100
ELIMINATION_THRESHOLD=0.7
```

## 🛠️ Development

### Local Development (without Docker)

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt

# Run FastAPI with hot reload
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

### Adding New Features

1. Create feature branch: `git checkout -b feature/new-feature`
2. Make changes and test locally
3. Run tests: `pytest`
4. Commit: `git commit -m "feat: add new feature"`
5. Push and create PR

## 📚 References

- [Wood Engineering](https://www.woodplc.com/)
- [ASME B31.3 Process Piping](https://www.asme.org/codes-standards/find-codes-standards/b31-3-process-piping)
- [API 570 Piping Inspection](https://www.api.org/products-and-services/individual-certification-programs/api-570)

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 👨‍💻 Authors

- **Aaron Sequeira** - [@aaron-seq](https://github.com/aaron-seq)
- Based on innovation project by Jeffrey Anokye, Jason Strouse, and Mariana Lima at Wood Engineering

## 🙏 Acknowledgments

- Wood Engineering for the original CML Optimization project
- Open-source ML community for excellent tools (scikit-learn, XGBoost, SHAP)
- Industrial datasets community for public corrosion datasets

---

**Status**: 🚧 Active Development | **Version**: 1.0.0 | **Last Updated**: December 2025
