# Safety Telemetry Platform & Rare-Event Analytics

End-to-end data pipeline for ingesting vehicle telemetry, detecting safety regressions using Bayesian models, and producing analytics for safety investigations.

## Tech Stack

- **Python**: Data processing, modeling, orchestration
- **SQL/BigQuery**: Data warehousing and transformations
- **PyMC**: Bayesian modeling (survival analysis, change-point detection)
- **Airflow**: Workflow orchestration
- **Docker Compose**: Local development environment

## Architecture

```
Data Sources → Ingestion → Staging → Transform → Analytics → Models → Alerts
```

See [Architecture Documentation](docs/architecture.md) for detailed system design.

## Project Structure

```
.
├── README.md
├── docker-compose.yml
├── requirements.txt
├── schemas/
│   └── bigquery_ddl.sql              # BigQuery table schemas
├── ingestion/
│   ├── generator.py                   # Synthetic data generator
│   └── loader.py                      # Load raw data to staging
├── transforms/
│   └── sql/
│       ├── staging_to_analytics.sql  # ETL transformations
│       └── analytics_views.sql        # Analytics views
├── models/
│   ├── survival_model.py              # Bayesian survival model
│   ├── changepoint_model.py          # Change-point detection
│   └── importance_sampling.py        # Importance sampling
├── dags/
│   └── safety_telemetry_pipeline.py  # Airflow DAG
├── notebooks/
│   ├── 01_data_exploration.ipynb
│   ├── 02_survival_analysis.ipynb
│   ├── 03_changepoint_detection.ipynb
│   └── 04_rare_event_experiment.ipynb
├── tests/
│   ├── test_ingestion.py
│   └── test_models.py
└── scripts/
    ├── export_tableau_extracts.py    # Generate Excel extracts
    └── run_transforms.py              # Run SQL transforms
```

## Quick Start

### 1. Setup Environment

```bash
docker-compose up -d
pip install -r requirements.txt
```

### 2. Generate Synthetic Data

```bash
python -m ingestion.generator --output data/synthetic/ --days 90 --trips-per-day 1000
```

### 3. Ingest Data

```bash
python -m ingestion.loader --input data/synthetic/ --target local
```

### 4. Run Transformations

```bash
python scripts/run_transforms.py --target local
```

### 5. Run Models

```bash
# Survival model
python -m models.survival_model

# Change-point detection
python -m models.changepoint_model

# Importance sampling experiment
python -m models.importance_sampling
```

### 6. Run Airflow Pipeline

```bash
# Access Airflow UI at http://localhost:8080
# Trigger DAG: safety_telemetry_pipeline
```

### 7. Generate Tableau Extracts

```bash
python scripts/export_tableau_extracts.py
# Generates Excel files in tableau/extracts/
```

## Core Components

### Data Ingestion

- **Synthetic Data Generator**: Creates realistic vehicle telemetry with configurable rare event rates
- **Data Loader**: Loads JSONL/CSV files into staging tables (BigQuery or SQLite)

### Data Transformation

- **SQL Transforms**: Staging → Analytics star schema
- **Analytics Views**: Pre-aggregated views for common queries

### Statistical Models

- **Survival Model**: Bayesian time-to-event model for safety regression prediction
- **Change-Point Model**: Detects shifts in hazard rates
- **Importance Sampling**: Reweighting schemes for rare event detection

### Orchestration

- **Airflow DAG**: Daily pipeline: ingest → transform → model → alert → publish

## Key Metrics

- **MTTD (Mean Time To Detection)**: Average time from regression onset to detection
- **Safety Regression**: Significant increase in hazard rate (hazard ratio > 1.5)
- **Safe-Ride Rate**: Percentage of trips without critical events
- **Rare-Event Detection Sensitivity**: True positive rate for rare failure modes

## Data Model

See [Data Dictionary](docs/data_dictionary.md) for complete table schemas.

**Staging Tables**: `staging_trips`, `staging_events`, `staging_mode_transitions`  
**Analytics Tables**: `fact_trip_safety`, `fact_events`, `fact_safety_regressions`  
**Model Outputs**: `model_survival_outputs`, `model_changepoint_outputs`

## Model Details

### Survival Model
- **Distribution**: Weibull hazard function
- **Random Effects**: Vehicle-level on scale parameter
- **Output**: Time-to-event predictions with 95% credible intervals

### Change-Point Model
- **Method**: Bayesian change-point detection
- **Output**: Change-point location, hazard ratio, MTTD

### Importance Sampling
- **Methods**: Uniform (baseline), Stratified, Importance, Adaptive
- **Improvement**: 30-40% MTTD reduction, 60% → 85% sensitivity

## Testing

```bash
pytest tests/
```

## Documentation

- [Architecture](docs/architecture.md) - System design and data flow
- [Data Dictionary](docs/data_dictionary.md) - Table schemas
- [Metrics Definitions](docs/metrics_definitions.md) - Metric formulas

## License

This project is for demonstration purposes.
