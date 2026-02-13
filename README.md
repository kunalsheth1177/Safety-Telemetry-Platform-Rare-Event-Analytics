# Safety Telemetry Platform & Rare-Event Analytics

End-to-end pipeline for ingesting event telemetry, modeling rare safety regressions, and producing dashboards + alerts for weekly safety investigations.

## Tech Stack
- **Python**: Data processing, modeling, orchestration
- **SQL/BigQuery**: Data warehousing and transformations
- **PyMC**: Bayesian modeling (survival analysis, change-point detection)
- **Airflow**: Workflow orchestration
- **Tableau**: Dashboards and visualizations
- **Docker Compose**: Local development environment

## Project Structure

```
.
├── README.md
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── docs/
│   ├── architecture.md
│   ├── data_dictionary.md
│   ├── metrics_definitions.md
│   ├── dashboard_spec.md
│   └── interview_narrative.md
├── schemas/
│   └── bigquery_ddl.sql
├── data/
│   ├── raw/          # Raw JSONL/CSV files
│   ├── staging/      # Staging tables (local SQLite for dev)
│   └── synthetic/    # Generated synthetic data
├── ingestion/
│   ├── __init__.py
│   ├── generator.py  # Synthetic data generator
│   └── loader.py     # Load raw data to staging
├── transforms/
│   ├── __init__.py
│   └── sql/
│       ├── staging_to_analytics.sql
│       └── analytics_views.sql
├── models/
│   ├── __init__.py
│   ├── survival_model.py
│   ├── changepoint_model.py
│   └── importance_sampling.py
├── notebooks/
│   ├── 01_data_exploration.ipynb
│   ├── 02_survival_analysis.ipynb
│   ├── 03_changepoint_detection.ipynb
│   └── 04_rare_event_experiment.ipynb
├── dags/
│   └── safety_telemetry_pipeline.py
├── tests/
│   ├── test_ingestion.py
│   ├── test_transforms.py
│   └── test_models.py
└── scripts/
    ├── setup_local_bq.sh
    └── run_pipeline.sh
```

## Quick Start

1. **Setup Environment**
```bash
docker-compose up -d
pip install -r requirements.txt
```

2. **Generate Synthetic Data**
```bash
python -m ingestion.generator --output data/synthetic/ --days 90 --trips-per-day 1000
```

3. **Run Ingestion**
```bash
python -m ingestion.loader --input data/synthetic/ --target staging
```

4. **Run Transformations**
```bash
# Execute SQL transforms (adapt for your DB)
python scripts/run_transforms.py
```

5. **Run Models**
```bash
python -m models.survival_model
python -m models.changepoint_model
```

6. **Run Airflow DAG**
```bash
# Access Airflow UI at http://localhost:8080
# Trigger DAG: safety_telemetry_pipeline
```

7. **Generate Tableau Extracts**
```bash
python scripts/export_tableau_extracts.py
# Extracts saved to tableau/extracts/
```

## Key Metrics

- **MTTD (Mean Time To Detection)**: Average time from safety regression onset to detection
- **Safety Regression**: Significant increase in hazard rate of critical safety events
- **Safe-Ride Rate**: Percentage of trips completed without critical safety interventions
- **Rare-Event Detection Sensitivity**: Ability to detect rare failure modes with low false positive rate

## Limitations & Next Steps

### Current Limitations

1. **Synthetic Data**: Uses generated data, not real vehicle telemetry. Real data would require schema adaptations and validation.
2. **Local Development Focus**: Optimized for local Docker setup. GCP deployment requires additional configuration (service accounts, IAM, etc.).
3. **Model Complexity**: PyMC models can be slow for large datasets. Consider approximate methods (ADVI, NUTS with fewer samples) for production.
4. **Real-Time Processing**: Current pipeline is daily batch. Real-time streaming would require Kafka/Pub/Sub integration.
5. **Alert Delivery**: Alert generation is implemented but email/Slack integration requires external service configuration.
6. **Power BI**: Dashboard spec provided but actual Power BI file not included (requires Power BI Desktop and BigQuery connection).

### Next Steps

**Short-Term (1-2 months)**:
- Integrate real vehicle telemetry data sources
- Add real-time alerting for critical regressions
- Implement automated model retraining pipeline
- Add A/B testing framework for detection thresholds

**Medium-Term (3-6 months)**:
- Causal inference to understand regression root causes
- Predictive maintenance models
- Multi-vehicle hierarchical models
- Model explainability (SHAP/LIME)

**Long-Term (6-12 months)**:
- Federated learning across vehicle fleets
- Reinforcement learning for threshold optimization
- Safety scenario simulation
- Regulatory compliance features

## Documentation

- **[Architecture](docs/architecture.md)**: System design and data flow
- **[Data Dictionary](docs/data_dictionary.md)**: Table schemas and column definitions
- **[Metrics Definitions](docs/metrics_definitions.md)**: All metric formulas and interpretations
- **[Dashboard Spec](docs/dashboard_spec.md)**: Power BI dashboard design
- **[Interview Narrative](docs/interview_narrative.md)**: 60-second overview and 2-minute deep dive

## Testing

Run tests with:
```bash
pytest tests/
```

## Contributing

This is a demonstration project. For production use:
1. Add comprehensive error handling
2. Implement data quality checks
3. Add monitoring and alerting
4. Secure credentials and API keys
5. Add unit and integration tests

## License

This project is for demonstration purposes.
