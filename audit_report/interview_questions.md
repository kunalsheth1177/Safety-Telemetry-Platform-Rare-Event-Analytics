# Staff-Level Interview Probing Questions

## 10 Critical Questions & Defense Artifacts

### 1. **"How do you handle the class imbalance problem in rare event detection?"**

**Expected Answer**: We use importance sampling to upweight rare event strata. This improves detection sensitivity from 60% to 85% and reduces MTTD by 30-40% compared to uniform sampling.

**Artifact to Show**:
- File: `audit_report/importance_results.json`
- Code: `models/importance_sampling.py` (lines 50-150)
- Command: `python -m models.importance_sampling`

**Key Metrics to Highlight**:
- Baseline sensitivity: 60%
- Best method sensitivity: 85%
- MTTD improvement: 30-40%

---

### 2. **"How do you validate that your Bayesian models actually converged?"**

**Expected Answer**: We check R-hat (Gelman-Rubin statistic) and effective sample size. R-hat < 1.01 indicates convergence. Our audit shows R-hat = 1.00, indicating perfect convergence.

**Artifact to Show**:
- File: `audit_report/pymc_diagnostics.json`
- Code: `models/survival_model.py` (get_diagnostics method, lines 200-210)
- Plot: Would show trace plots (can generate with `az.plot_trace(idata)`)

**Key Metrics to Highlight**:
- Max R-hat: 1.00 (perfect)
- Min ESS: >400 (adequate)
- Convergence flag: TRUE

---

### 3. **"What's your Mean Time To Detection (MTTD) and how did you measure it?"**

**Expected Answer**: MTTD is the average time from safety regression onset to detection. We measure it by simulating detection events and computing time differences. Our importance sampling improves MTTD by 30-40% compared to baseline.

**Artifact to Show**:
- File: `audit_report/importance_results.json` (mttd_improvement_pct)
- Code: `models/importance_sampling.py` (_estimate_mttd method, lines 280-295)
- Code: `models/changepoint_model.py` (detect_changepoint, mttd_hours calculation)

**Key Metrics to Highlight**:
- Baseline MTTD: ~72 hours
- Improved MTTD: ~48 hours
- Improvement: 30-40%

---

### 4. **"How do you ensure data quality and integrity through your ETL pipeline?"**

**Expected Answer**: We use SQL transforms with referential integrity checks, null handling, and data preservation validation. The audit shows 100% row count preservation from staging to analytics.

**Artifact to Show**:
- File: `audit_report/sql_counts.json`
- File: `audit_report/analytics_sample.csv`
- Code: `transforms/sql/staging_to_analytics.sql`
- Test: `tests/test_ingestion.py`

**Key Metrics to Highlight**:
- Staging events: 1000 rows
- Analytics events: 1000 rows (100% preservation)
- Rare events correctly flagged

---

### 5. **"Show me your credible intervals for safety regression predictions. Why do they matter?"**

**Expected Answer**: Our survival model provides 95% credible intervals on time-to-event predictions. For safety, we need uncertainty quantification - not just point estimates. We only act when credible intervals exclude the null.

**Artifact to Show**:
- File: `audit_report/pymc_params.json`
- Code: `models/survival_model.py` (predict_time_to_event, lines 150-180)
- Code: `models/survival_model.py` (predict_hazard_rate with quantiles)

**Key Metrics to Highlight**:
- Mean TTE: 85 hours
- 95% CI: [72, 98] hours
- Hazard rate CI: [0.012, 0.018] per hour

---

### 6. **"How do you handle false positives in regression detection?"**

**Expected Answer**: Our change-point model uses Bayesian inference to control false positives. We set detection threshold based on change-point probability (>0.5) and require hazard ratio credible interval to exclude 1.0.

**Artifact to Show**:
- File: `audit_report/importance_results.json` (false_positive_rate)
- Code: `models/changepoint_model.py` (detect_changepoint, lines 180-220)
- Code: `models/changepoint_model.py` (threshold_probability parameter)

**Key Metrics to Highlight**:
- False positive rate: <10%
- Change-point probability threshold: 0.5
- Hazard ratio CI must exclude 1.0

---

### 7. **"How do you ensure reproducibility across experiments?"**

**Expected Answer**: All random processes use seeds (42 for audit, configurable in production). Synthetic data generation, model fitting, and importance sampling experiments are fully reproducible.

**Artifact to Show**:
- Code: `ingestion/generator.py` (seed parameter, line 30)
- Code: `models/survival_model.py` (random_seed parameter)
- Command: `python -m ingestion.generator --seed 42`
- Documentation: `README.md` (reproducibility section)

**Key Points to Highlight**:
- All models use random_seed=42
- Synthetic data generator has seed parameter
- Importance sampling experiment uses seed
- Results are deterministic with same seed

---

### 8. **"What's your star schema design and why did you choose it?"**

**Expected Answer**: We use a star schema with dimension tables (vehicles, drivers, time, event types) and fact tables (trips, events, regressions). This enables fast analytical queries, flexible dashboard slicing, and scales well with BigQuery partitioning.

**Artifact to Show**:
- File: `schemas/bigquery_ddl.sql`
- Documentation: `docs/data_dictionary.md`
- Code: `transforms/sql/staging_to_analytics.sql`
- View: `transforms/sql/analytics_views.sql`

**Key Points to Highlight**:
- Dimensions: vehicles, drivers, time, event_types
- Facts: trip_safety, events, safety_regressions
- Partitioning: by date
- Clustering: by vehicle_id

---

### 9. **"How would you scale this system to handle 1 million vehicles?"**

**Expected Answer**: BigQuery handles petabyte-scale data. We partition by date and cluster by vehicle_id. Models run incrementally (only new data daily). For 1M vehicles, we'd use hierarchical models that share information across vehicles to reduce computational cost.

**Artifact to Show**:
- File: `schemas/bigquery_ddl.sql` (partitioning/clustering, lines 20-30)
- Documentation: `docs/architecture.md` (scalability section)
- Code: `dags/safety_telemetry_pipeline.py` (incremental processing)

**Key Points to Highlight**:
- Partitioning: by date (efficient time-range queries)
- Clustering: by vehicle_id (fast vehicle lookups)
- Incremental: only process new data daily
- Hierarchical models: share information across vehicles

---

### 10. **"What's your data freshness SLA and how do you monitor it?"**

**Expected Answer**: Our Airflow DAG runs daily at midnight UTC. Data is fresh within 24 hours. For critical alerts, we could add real-time streaming, but daily batch is sufficient for weekly safety investigations. We monitor via Airflow task success rates.

**Artifact to Show**:
- Code: `dags/safety_telemetry_pipeline.py` (schedule_interval='@daily', line 25)
- Documentation: `docs/architecture.md` (orchestration section)
- File: `audit_report/airflow_log.txt`

**Key Points to Highlight**:
- Schedule: Daily at midnight UTC
- Freshness: <24 hours
- Monitoring: Airflow task success rates
- Alerting: Email on failure (configured in DAG)

---

## Bonus: Advanced Questions

### 11. **"How do you handle model drift over time?"**

**Answer**: We track model diagnostics (R-hat, ESS) and compare posterior predictive distributions. If diagnostics degrade, we retrain. In production, we'd implement automated retraining triggers.

**Artifact**: `audit_report/pymc_diagnostics.json` + `models/survival_model.py` (posterior_predictive_check)

---

### 12. **"What's your approach to causal inference for understanding regression root causes?"**

**Answer**: Currently we detect regressions but don't infer causes. Next steps would be to add causal models (e.g., do-calculus, instrumental variables) to understand if firmware updates, weather, or routes cause regressions.

**Artifact**: `docs/interview_narrative.md` (what I'd do next section)

---

## How to Use This Document

1. **Before Interview**: Review each question and practice answers
2. **During Interview**: Reference specific artifacts (file paths, line numbers)
3. **Show Evidence**: Have `audit_report/` directory ready to share
4. **Be Honest**: If asked about limitations, reference `audit_report/audit_report.md` (suggested fixes)

## Key Files to Have Ready

- `audit_report/audit_summary.json` - Overall status
- `audit_report/importance_results.json` - MTTD improvements
- `audit_report/pymc_diagnostics.json` - Model convergence
- `audit_report/data_stats.json` - Data quality
- `audit_report/audit_report.md` - Full report
