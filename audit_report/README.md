# Audit Report Directory

This directory contains comprehensive audit results for the Safety Telemetry Platform.

## Quick Start

To run the full audit:

```bash
# From project root
./run_audit.sh

# Or manually
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python audit_report/audit_runner.py
```

## Files Generated

### Core Reports
- `audit_summary.json` - Complete audit results in JSON format
- `audit_report.md` - Human-readable comprehensive report
- `interview_questions.md` - 10 staff-level questions with defense artifacts

### Data Artifacts
- `data_sample.csv` - Sample synthetic data (1000 rows)
- `data_stats.json` - Data generation statistics
- `analytics_sample.csv` - Sample analytics table (10 rows)
- `sql_counts.json` - SQL transform validation results

### Model Artifacts
- `pymc_diagnostics.json` - Model convergence diagnostics (R-hat, ESS)
- `pymc_params.json` - Model parameter estimates with credible intervals
- `importance_results.json` - Importance sampling experiment results

### Test Artifacts
- `test_report.txt` - Unit test execution results
- `airflow_log.txt` - Airflow DAG validation log
- `sample_alerts.csv` - Sample alert events

### Specifications
- `dashboard_spec.json` - Dashboard specification export

## Evidence for Interviews

When asked about specific aspects, reference these files:

1. **Rare event detection**: `importance_results.json`
2. **Model convergence**: `pymc_diagnostics.json`
3. **MTTD improvement**: `importance_results.json` (mttd_improvement_pct)
4. **Data quality**: `sql_counts.json` + `analytics_sample.csv`
5. **Uncertainty quantification**: `pymc_params.json`
6. **Pipeline orchestration**: `airflow_log.txt`

See `interview_questions.md` for detailed Q&A with artifact references.

## Reproducibility

All audit results are reproducible with:
- Fixed random seeds (42)
- Deterministic synthetic data generation
- Versioned dependencies (requirements.txt)

Run `./run_audit.sh` to regenerate all artifacts.
