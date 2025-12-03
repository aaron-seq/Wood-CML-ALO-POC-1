# Wood AI CML Optimization - Setup Guide

## 🚀 Quick Start (5 Minutes)

### Prerequisites
- Docker & Docker Compose installed
- Git installed
- 4GB RAM minimum
- Internet connection for downloading images

### Step 1: Clone Repository
```bash
git clone https://github.com/aaron-seq/Wood-AI-CML-ALO-Machine-Learning-Model.git
cd Wood-AI-CML-ALO-Machine-Learning-Model
```

### Step 2: Configure Environment
```bash
cp .env.example .env
```

Optionally edit `.env` to customize:
- Database credentials
- ML model thresholds
- Logging configuration

### Step 3: Start Services
```bash
docker-compose up --build
```

Wait for:
- ✅ PostgreSQL: "database system is ready to accept connections"
- ✅ FastAPI: "Application startup complete"

### Step 4: Access Application

- **Main Dashboard**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 📊 Load Sample Data

### Option 1: Using API (Recommended)

1. Download sample data:
   - File: `CML_Optimization_Sample_Data.xlsx`
   - Place in: `data/raw/`

2. Upload via API:
```bash
curl -X POST "http://localhost:8000/api/v1/cml/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@data/raw/CML_Optimization_Sample_Data.xlsx"
```

3. Or use the Swagger UI:
   - Go to http://localhost:8000/docs
   - Navigate to POST `/api/v1/cml/upload`
   - Click "Try it out"
   - Upload the Excel file

### Option 2: Using Seed Script

```bash
# From host machine
docker-compose exec app python scripts/seed_database.py
```

## 🤖 Train ML Models

### Initial Training

```bash
# Train elimination prediction model
docker-compose exec app python scripts/train_models.py
```

This will:
1. Load CML data from database
2. Train XGBoost elimination model
3. Save model to `data/models/cml_elimination_model.pkl`
4. Log metrics to database

### Run Analysis

```bash
curl -X POST "http://localhost:8000/api/v1/cml/analyze" \
  -H "Content-Type: application/json" \
  -d '{"threshold": 0.7, "retrain": false}'
```

Or via Swagger UI:
- POST `/api/v1/cml/analyze`
- Set `threshold` (0.0-1.0) for elimination confidence
- Set `retrain: true` to retrain model

## 📈 Generate Forecasts

```bash
# Forecast for specific CML
curl -X POST "http://localhost:8000/api/v1/forecast/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "cml_id": "CML-C100-0001",
    "periods": 24,
    "model_type": "prophet"
  }'
```

Supported models:
- `prophet`: Facebook Prophet (recommended for seasonal data)
- `linear`: Linear regression (fast, simple)
- `arima`: ARIMA (coming soon)

## 📄 Generate Reports

### PDF Report

```bash
curl -X POST "http://localhost:8000/api/v1/report/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "facility": "Facility A",
    "include_forecasts": true,
    "include_shap": true
  }' \
  --output CML_Report.pdf
```

### Excel Export

```bash
curl "http://localhost:8000/api/v1/report/export-excel?facility=Facility A" \
  --output CML_Export.xlsx
```

## 🎛️ Dashboard Metrics

```bash
# Get all metrics
curl http://localhost:8000/api/v1/dashboard/metrics

# Risk matrix data
curl http://localhost:8000/api/v1/dashboard/risk-matrix

# Corrosion trends
curl http://localhost:8000/api/v1/dashboard/corrosion-trends

# Elimination summary
curl http://localhost:8000/api/v1/dashboard/elimination-summary
```

## 🔧 Development Setup

### Local Development (Without Docker)

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
cd backend
pip install -r requirements.txt

# Set up PostgreSQL locally or use Docker for DB only
docker run -d \
  -p 5432:5432 \
  -e POSTGRES_DB=cml_optimization \
  -e POSTGRES_USER=cml_user \
  -e POSTGRES_PASSWORD=cml_pass \
  postgres:16-alpine

# Run FastAPI
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Run Tests

```bash
# Inside container
docker-compose exec app pytest

# With coverage
docker-compose exec app pytest --cov=app --cov-report=html

# Specific test file
docker-compose exec app pytest backend/tests/test_api.py -v
```

### Code Quality

```bash
# Format code
docker-compose exec app black backend/app

# Lint
docker-compose exec app flake8 backend/app

# Type checking
docker-compose exec app mypy backend/app
```

## 📦 Data Schema

### Required Columns in Excel Upload

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| `CML_ID` | String | Yes | Unique identifier |
| `Facility` | String | No | Facility name |
| `Commodity` | String | No | Fluid/gas type |
| `Material_Type` | String | No | Pipe material |
| `Feature_Type` | String | No | Elbow, Tee, etc. |
| `Current_Thickness_mm` | Float | Yes | Latest measurement |
| `Min_Allowable_Thickness_mm` | Float | Yes | Minimum safe thickness |
| `Average_Corrosion_Rate_mm_per_year` | Float | Yes | Calculated rate |
| `Remaining_Life_Years` | Float | Yes | Estimated life |
| `Risk_Level` | String | No | Critical/High/Medium/Low |
| `Inspection_History_Dates` | String | No | Pipe-delimited dates |
| `Inspection_History_Measurements` | String | No | Pipe-delimited values |

See `data/raw/CML_Optimization_Sample_Data.xlsx` for complete example.

## 🐛 Troubleshooting

### Database Connection Issues

```bash
# Check PostgreSQL logs
docker-compose logs db

# Verify connection from app container
docker-compose exec app psql -h db -U cml_user -d cml_optimization
```

### Model Training Fails

```bash
# Check if data exists
docker-compose exec app python -c "from backend.app.core.database import SessionLocal; from backend.app.models.db_models import CML; print(SessionLocal().query(CML).count())"

# View app logs
docker-compose logs app
```

### API Returns 500 Errors

1. Check logs: `docker-compose logs app | tail -50`
2. Verify database is running: `docker-compose ps`
3. Test health endpoint: `curl http://localhost:8000/health`
4. Restart services: `docker-compose restart`

### Port Already in Use

```bash
# Change ports in docker-compose.yml
ports:
  - "8001:8000"  # Changed from 8000:8000
```

## 🔐 Production Deployment

### Security Checklist

- [ ] Change all default passwords in `.env`
- [ ] Set `DEBUG=False`
- [ ] Use strong `SECRET_KEY`
- [ ] Enable HTTPS/TLS
- [ ] Restrict `ALLOWED_ORIGINS`
- [ ] Set up firewall rules
- [ ] Enable database backups
- [ ] Use secrets management (e.g., AWS Secrets Manager)

### Cloud Deployment Options

#### AWS ECS/Fargate
1. Push images to ECR
2. Create ECS task definitions
3. Set up RDS PostgreSQL
4. Configure Application Load Balancer
5. Use Secrets Manager for credentials

#### Azure Container Instances
1. Push to Azure Container Registry
2. Create Container Group
3. Use Azure Database for PostgreSQL
4. Configure Application Gateway

#### Google Cloud Run
1. Build and push to GCR
2. Deploy Cloud Run services
3. Use Cloud SQL PostgreSQL
4. Set up Cloud Load Balancing

## 📚 API Reference

See interactive documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/v1/cml/upload` | POST | Upload Excel data |
| `/api/v1/cml/summary` | GET | Get CML summary |
| `/api/v1/cml/analyze` | POST | Run ML analysis |
| `/api/v1/forecast/predict` | POST | Generate forecast |
| `/api/v1/report/generate` | POST | Create PDF report |
| `/api/v1/dashboard/metrics` | GET | Dashboard metrics |

## 🤝 Contributing

1. Fork repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

## 📞 Support

- **Issues**: https://github.com/aaron-seq/Wood-AI-CML-ALO-Machine-Learning-Model/issues
- **Email**: aaron_seq@outlook.com
- **LinkedIn**: [Aaron Sequeira](https://www.linkedin.com/in/aaron-sequeira)

## 📝 License

MIT License - see LICENSE file for details.

---

**Last Updated**: December 2025 | **Version**: 1.0.0
