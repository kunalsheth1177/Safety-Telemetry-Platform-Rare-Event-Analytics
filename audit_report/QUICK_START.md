# Quick Start - Running the Audit

## One-Command Audit

```bash
./run_audit.sh
```

This will:
1. Create Python virtual environment
2. Install all dependencies
3. Run comprehensive audit
4. Generate all artifacts in `audit_report/`

## Manual Steps

```bash
# 1. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run audit
python audit_report/audit_runner.py
```

## Expected Output

The audit will generate:
- ✅ `audit_summary.json` - Complete results (printed to stdout)
- ✅ `audit_report.md` - Human-readable report
- ✅ `data_sample.csv` - Sample synthetic data
- ✅ `pymc_diagnostics.json` - Model convergence
- ✅ `importance_results.json` - MTTD improvements
- ✅ All other artifacts in `audit_report/`

## Troubleshooting

**Issue**: `ModuleNotFoundError`
**Fix**: Run `pip install -r requirements.txt`

**Issue**: PyMC models take too long
**Fix**: Models use reduced samples (200) for audit speed. Production uses 2000.

**Issue**: Airflow DAG import fails
**Fix**: This is expected - full Airflow requires Docker. Audit validates syntax only.

## Next Steps

1. Review `audit_report/audit_report.md` for full results
2. Review `audit_report/STAFF_QUESTIONS.md` for interview prep
3. Check `audit_report/audit_summary.json` for status
