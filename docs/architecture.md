# System Architecture

## Overview
The Safety Telemetry Platform is an end-to-end data pipeline that ingests vehicle telemetry, models safety regressions, and produces actionable insights through dashboards and alerts.

## Architecture Diagram (Text Description)

```
┌─────────────────────────────────────────────────────────────────┐
│                    DATA SOURCES                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Vehicle      │  │ Event        │  │ Mode         │         │
│  │ Telemetry    │  │ Logs         │  │ Transitions  │         │
│  │ (JSONL/CSV)  │  │ (JSONL/CSV)  │  │ (JSONL/CSV)  │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    INGESTION LAYER                               │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  Synthetic Data Generator (for development/testing)       │ │
│  │  - Generates realistic trip, event, transition data       │ │
│  │  - Configurable rare event rates                         │ │
│  │  - Temporal patterns (regressions, improvements)         │ │
│  └──────────────────────────────────────────────────────────┘ │
│                            │                                     │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  Data Loader                                              │ │
│  │  - Reads JSONL/CSV files                                  │ │
│  │  - Validates schemas                                     │ │
│  │  - Loads to staging tables                                │ │
│  └──────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    STAGING LAYER (BigQuery)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ staging_trips│  │staging_events│  │staging_      │         │
│  │              │  │              │  │mode_trans    │         │
│  │ Raw ingested │  │ Raw ingested │  │Raw ingested  │         │
│  │ data         │  │ data         │  │data          │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    TRANSFORMATION LAYER                         │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  SQL Transformations (Airflow)                           │ │
│  │  - Staging → Analytics (Star Schema)                     │ │
│  │  - Dimension tables (vehicles, drivers, time, events)    │ │
│  │  - Fact tables (trips, events, regressions)              │ │
│  │  - Data quality checks                                   │ │
│  └──────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ANALYTICS LAYER (BigQuery)                   │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  Star Schema:                                            │ │
│  │  - dim_vehicles, dim_drivers, dim_time, dim_event_types  │ │
│  │  - fact_trip_safety, fact_events, fact_safety_regressions│ │
│  │  - Analytics views (v_daily_safety_summary, etc.)        │ │
│  └──────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    MODELING LAYER (PyMC)                        │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  Survival Model                                          │ │
│  │  - Weibull hazard function                               │ │
│  │  - Vehicle-level random effects                         │ │
│  │  - Time-to-event predictions                            │ │
│  │  - Credible intervals                                   │ │
│  └──────────────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  Change-Point Model                                      │ │
│  │  - Bayesian change-point detection                      │ │
│  │  - Pre/post change hazard rates                         │ │
│  │  - MTTD calculation                                     │ │
│  │  - Regression episode identification                    │ │
│  └──────────────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  Importance Sampling                                     │ │
│  │  - Rare event reweighting                               │ │
│  │  - Detection sensitivity improvement                    │ │
│  │  - MTTD optimization                                     │ │
│  └──────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    MODEL OUTPUTS (BigQuery)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │model_survival│  │model_        │  │model_        │         │
│  │_outputs      │  │changepoint_  │  │importance_   │         │
│  │              │  │outputs       │  │sampling_     │         │
│  │Hazard rates, │  │Change-points,│  │results       │         │
│  │predictions   │  │MTTD          │  │Sensitivity   │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATION (Airflow)                      │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  Daily DAG: safety_telemetry_pipeline                    │ │
│  │  1. Ingest data → staging                                │ │
│  │  2. Transform → analytics                                 │ │
│  │  3. Run models (survival, changepoint, importance)        │ │
│  │  4. Generate alerts                                       │ │
│  │  5. Publish results → BigQuery                            │ │
│  └──────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    VISUALIZATION & ALERTS                       │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  Power BI Dashboard                                       │ │
│  │  - Executive summary                                      │ │
│  │  - Regression analysis                                    │ │
│  │  - Rare event detection                                   │ │
│  │  - Vehicle performance                                    │ │
│  │  - Model diagnostics                                      │ │
│  └──────────────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  Alert System                                             │ │
│  │  - Regression detection alerts                           │ │
│  │  - Threshold-based notifications                         │ │
│  │  - Email notifications                                   │ │
│  │  - Dashboard alerts table                                │ │
│  └──────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Data Sources
- **Format**: JSONL (JSON Lines) or CSV
- **Schema**: Trips, events, mode transitions
- **Volume**: ~1000 trips/day, ~10-50 events/trip
- **Latency**: Near real-time (batch daily)

### 2. Ingestion Layer
- **Synthetic Generator**: Python script for development/testing
- **Data Loader**: Validates and loads to staging
- **Targets**: BigQuery (production) or SQLite (local dev)

### 3. Staging Layer
- **Purpose**: Raw data storage before transformation
- **Tables**: `staging_trips`, `staging_events`, `staging_mode_transitions`
- **Partitioning**: By date for efficient queries
- **Clustering**: By vehicle_id, timestamp

### 4. Transformation Layer
- **Technology**: SQL (BigQuery SQL dialect)
- **Process**: ETL from staging to analytics star schema
- **Quality Checks**: Data validation, null handling, deduplication

### 5. Analytics Layer
- **Schema**: Star schema (dimensions + facts)
- **Optimization**: Partitioned by date, clustered by vehicle
- **Views**: Pre-aggregated for common queries

### 6. Modeling Layer
- **Framework**: PyMC (Bayesian modeling)
- **Models**:
  - Survival: Time-to-event for safety regressions
  - Change-point: Detect shifts in hazard rates
  - Importance Sampling: Improve rare event detection
- **Output**: Credible intervals, predictions, diagnostics

### 7. Orchestration
- **Tool**: Apache Airflow
- **Schedule**: Daily at midnight UTC
- **Dependencies**: Sequential and parallel tasks
- **Error Handling**: Retries, alerts on failure

### 8. Visualization
- **Tool**: Power BI
- **Data Source**: BigQuery (DirectQuery or Import)
- **Refresh**: Daily after pipeline completion
- **Users**: Safety engineers, leadership, analysts

## Data Flow

1. **Ingestion** (Daily)
   - Raw files arrive (or generated synthetically)
   - Loader validates and ingests to staging

2. **Transformation** (Daily, after ingestion)
   - SQL transforms create analytics tables
   - Data quality checks run

3. **Modeling** (Daily, after transformation)
   - Survival model: Predicts time-to-regression
   - Change-point model: Detects regression shifts
   - Importance sampling: Evaluates detection methods

4. **Alerting** (Daily, after modeling)
   - Alerts generated for detected regressions
   - Threshold-based notifications

5. **Visualization** (Continuous)
   - Power BI queries BigQuery
   - Dashboards update with latest data

## Scalability Considerations

- **BigQuery**: Handles petabyte-scale data
- **Partitioning**: By date for efficient queries
- **Clustering**: By vehicle_id for fast lookups
- **Incremental Processing**: Only process new data
- **Model Caching**: Cache model outputs for reuse

## Security

- **Authentication**: GCP service accounts
- **Authorization**: BigQuery IAM roles
- **Encryption**: At rest and in transit
- **Audit Logging**: All data access logged

## Monitoring

- **Airflow**: Task success/failure rates
- **BigQuery**: Query performance, slot usage
- **Models**: Convergence diagnostics (R-hat, ESS)
- **Alerts**: Alert generation and delivery

## Local Development

- **Docker Compose**: Airflow, PostgreSQL
- **SQLite**: Local database for staging/analytics
- **Synthetic Data**: Generator creates realistic test data
- **No GCP Required**: Full pipeline runs locally
