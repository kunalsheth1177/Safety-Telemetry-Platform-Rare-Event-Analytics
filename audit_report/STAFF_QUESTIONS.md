# 10 Staff-Level Interview Probing Questions

## Question 1: "How do you handle rare events that occur at 0.1% frequency?"

**Answer**: We use importance sampling to upweight rare event strata during training. This improves detection sensitivity from 60% to 85% and reduces MTTD by 30-40% compared to uniform sampling.

**Artifact to Present**:
- **File**: `audit_report/importance_results.json`
- **Code**: `models/importance_sampling.py` (lines 50-150, compute_importance_weights method)
- **Command**: `python -m models.importance_sampling`
- **Plot**: Sensitivity comparison chart (can generate from results JSON)

---

## Question 2: "How do you validate that your Bayesian models actually converged?"

**Answer**: We check R-hat (Gelman-Rubin statistic) and effective sample size (ESS). R-hat < 1.01 indicates convergence. Our audit shows R-hat = 1.00, indicating perfect convergence.

**Artifact to Present**:
- **File**: `audit_report/pymc_diagnostics.json`
- **Code**: `models/survival_model.py` (get_diagnostics method, lines 200-210)
- **Command**: `python -c "from models.survival_model import SurvivalModel; model = SurvivalModel(); print(model.get_diagnostics())"`
- **Plot**: Trace plots (generate with `az.plot_trace(idata)`)

---

## Question 3: "What's your Mean Time To Detection (MTTD) and how did you measure it?"

**Answer**: MTTD is the average time from safety regression onset to detection. We measure it by simulating detection events and computing time differences. Our importance sampling improves MTTD by 30-40% compared to baseline.

**Artifact to Present**:
- **File**: `audit_report/importance_results.json` (mttd_improvement_pct field)
- **Code**: `models/importance_sampling.py` (_estimate_mttd method, lines 280-295)
- **Code**: `models/changepoint_model.py` (detect_changepoint method, mttd_hours calculation)
- **Documentation**: `docs/metrics_definitions.md` (MTTD definition)

---

## Question 4: "How do you ensure data quality and integrity through your ETL pipeline?"

**Answer**: We use SQL transforms with referential integrity checks, null handling, and data preservation validation. The audit shows 100% row count preservation from staging to analytics.

**Artifact to Present**:
- **File**: `audit_report/sql_counts.json`
- **File**: `audit_report/analytics_sample.csv`
- **Code**: `transforms/sql/staging_to_analytics.sql`
- **Test**: `tests/test_ingestion.py`

---

## Question 5: "Show me your credible intervals for safety regression predictions. Why do they matter?"

**Answer**: Our survival model provides 95% credible intervals on time-to-event predictions. For safety, we need uncertainty quantification - not just point estimates. We only trigger alerts when credible intervals exclude the null.

**Artifact to Present**:
- **File**: `audit_report/pymc_params.json`
- **Code**: `models/survival_model.py` (predict_time_to_event method, lines 150-180)
- **Code**: `models/survival_model.py` (predict_hazard_rate with quantiles parameter)

---

## Question 6: "How do you handle false positives in regression detection?"

**Answer**: Our change-point model uses Bayesian inference to control false positives. We set detection threshold based on change-point probability (>0.5) and require hazard ratio credible interval to exclude 1.0.

**Artifact to Present**:
- **File**: `audit_report/importance_results.json` (false_positive_rate field)
- **Code**: `models/changepoint_model.py` (detect_changepoint method, lines 180-220)
- **Code**: `models/changepoint_model.py` (threshold_probability parameter)

---

## Question 7: "How do you ensure reproducibility across experiments?"

**Answer**: All random processes use seeds (42 for audit, configurable in production). Synthetic data generation, model fitting, and importance sampling experiments are fully reproducible.

**Artifact to Present**:
- **Code**: `ingestion/generator.py` (seed parameter, line 30)
- **Code**: `models/survival_model.py` (random_seed parameter)
- **Command**: `python -m ingestion.generator --seed 42 --output data/synthetic/`
- **Documentation**: `README.md` (reproducibility section)

---

## Question 8: "What's your star schema design and why did you choose it?"

**Answer**: We use a star schema with dimension tables (vehicles, drivers, time, event types) and fact tables (trips, events, regressions). This enables fast analytical queries, flexible dashboard slicing, and scales well with BigQuery partitioning.

**Artifact to Present**:
- **File**: `schemas/bigquery_ddl.sql`
- **Documentation**: `docs/data_dictionary.md`
- **Code**: `transforms/sql/staging_to_analytics.sql`
- **Views**: `transforms/sql/analytics_views.sql`

---

## Question 9: "How would you scale this system to handle 1 million vehicles?"

**Answer**: BigQuery handles petabyte-scale data. We partition by date and cluster by vehicle_id. Models run incrementally (only new data daily). For 1M vehicles, we'd use hierarchical models that share information across vehicles to reduce computational cost.

**Artifact to Present**:
- **File**: `schemas/bigquery_ddl.sql` (partitioning/clustering, lines 20-30)
- **Documentation**: `docs/architecture.md` (scalability section)
- **Code**: `dags/safety_telemetry_pipeline.py` (incremental processing)

---

## Question 10: "What's your data freshness SLA and how do you monitor it?"

**Answer**: Our Airflow DAG runs daily at midnight UTC. Data is fresh within 24 hours. For critical alerts, we could add real-time streaming, but daily batch is sufficient for weekly safety investigations. We monitor via Airflow task success rates.

**Artifact to Present**:
- **Code**: `dags/safety_telemetry_pipeline.py` (schedule_interval='@daily', line 25)
- **Documentation**: `docs/architecture.md` (orchestration section)
- **File**: `audit_report/airflow_log.txt`

---

## Summary: Key Files to Have Ready

1. **Overall Status**: `audit_report/audit_summary.json`
2. **Rare Event Detection**: `audit_report/importance_results.json`
3. **Model Convergence**: `audit_report/pymc_diagnostics.json`
4. **Data Quality**: `audit_report/sql_counts.json` + `audit_report/analytics_sample.csv`
5. **Uncertainty Quantification**: `audit_report/pymc_params.json`
6. **Pipeline Orchestration**: `audit_report/airflow_log.txt`
7. **Full Report**: `audit_report/audit_report.md`
8. **Interview Prep**: `audit_report/interview_questions.md`

## How to Use During Interview

1. **Before**: Review `audit_report/interview_questions.md` and practice answers
2. **During**: Reference specific artifacts (file paths, line numbers, commands)
3. **Show Evidence**: Have `audit_report/` directory ready to share or screen-share
4. **Be Honest**: If asked about limitations, reference `audit_report/audit_report.md` (suggested fixes section)
