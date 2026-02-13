# Tableau Dashboard - Safety Telemetry Platform

## Overview

Tableau-compatible dashboard for weekly safety investigations with 4 interactive pages covering fleet safety, rare event monitoring, change-point detection, and MTTD comparison.

## Quick Start

### 1. Generate CSV Extracts

```bash
python scripts/export_tableau_extracts.py
```

This generates 5 CSV files in `tableau/extracts/`:
- `fleet_safety_overview.csv` - Daily fleet metrics (90 days)
- `rare_event_monitoring.csv` - Rare event details
- `changepoint_detection.csv` - Change-point detection results
- `mttd_comparison.csv` - MTTD comparison by method
- `vehicle_details.csv` - Vehicle metadata

### 2. Connect to Tableau

1. Open Tableau Desktop
2. Connect to Text File
3. Select CSV files from `tableau/extracts/`
4. Create relationships between data sources:
   - `fleet_safety_overview` ↔ `vehicle_details` (by Vehicle ID)
   - `rare_event_monitoring` ↔ `vehicle_details` (by Vehicle ID)
   - `changepoint_detection` ↔ `fleet_safety_overview` (by Date)

### 3. Build Dashboard

Follow the specification in `docs/tableau_dashboard_spec.md` to build:
- Page 1: Fleet Safety Overview
- Page 2: Rare Event Monitoring
- Page 3: Change-Point Detection
- Page 4: MTTD Comparison

### 4. Add Calculated Fields

Create calculated fields as specified in `tableau/tableau_dashboard_spec.json`:
- Intervention Rate
- Degraded Mode Rate
- Latency Bucket
- Rolling 7-Day Failure Rate
- Regression Status
- MTTD Improvement vs Baseline
- MTTD Improvement Percentage

### 5. Configure Filters & Parameters

Set up:
- Global filters (Date Range, Vehicle Model, Firmware Version)
- Parameters (Target Safe Ride Rate, Regression Threshold, Latency Threshold, Sensitivity Threshold)

## Dashboard Specification

See `docs/tableau_dashboard_spec.md` for complete specification including:
- Visual descriptions
- Calculated field formulas
- Filter configurations
- Parameter definitions
- Dashboard actions

## Weekly Workflow

See `docs/weekly_analyst_workflow.md` for:
- Monday morning routine (30 minutes)
- Weekly report generation (1 hour)
- Ad-hoc investigation procedures
- Best practices and troubleshooting

## Files

- `tableau/extracts/` - CSV data extracts
- `tableau/tableau_dashboard_spec.json` - Complete dashboard specification (JSON)
- `docs/tableau_dashboard_spec.md` - Human-readable specification
- `docs/weekly_analyst_workflow.md` - Analyst workflow guide
- `scripts/export_tableau_extracts.py` - Extract generation script

## Refresh Schedule

- **Daily**: After Airflow pipeline completion
- **Script**: Run `python scripts/export_tableau_extracts.py` daily
- **Tableau**: Refresh data sources or use Tableau Server scheduled refresh

## Next Steps

1. Connect CSV extracts in Tableau
2. Build calculated fields
3. Create 4 dashboard pages
4. Configure filters and parameters
5. Test workflow with `docs/weekly_analyst_workflow.md`
6. Publish to Tableau Server/Online
7. Schedule daily extract refresh
