# Power BI Dashboard Specification

## Overview
Interactive dashboard for weekly safety investigations, providing real-time visibility into safety metrics, regression detection, and rare event analysis.

## Data Source
- **Primary**: BigQuery dataset `safety_telemetry`
- **Refresh Schedule**: Daily (after Airflow pipeline completion)
- **Connection**: DirectQuery or Import (depending on data volume)

## Dashboard Pages

### Page 1: Executive Summary
**Purpose**: High-level safety overview for leadership

#### Visuals:
1. **KPI Cards (Top Row)**
   - Total Trips (Last 7 Days)
   - Safe Ride Rate (%)
   - Active Vehicles
   - Total Critical Events
   - Mean Time To Detection (MTTD) - Hours

2. **Safety Trend Line Chart**
   - X-axis: Date (Last 90 days)
   - Y-axis: Safe Ride Rate (%)
   - Series: Overall, by Vehicle Model
   - Slicers: Date Range, Vehicle Model

3. **Event Distribution Donut Chart**
   - Categories: Critical Events, Warnings, Info Events
   - Drill-through: Event Details page

4. **Regression Alerts Table**
   - Columns: Vehicle ID, Detection Date, Hazard Ratio, MTTD, Status
   - Filter: Last 30 days, Unresolved only
   - Action: Click to drill-through to Regression Details

5. **Top Vehicles by Safety Score**
   - Bar chart: Top 10 vehicles (highest safety score)
   - Tooltip: Total trips, Critical events, Rare events

#### Measures:
```dax
Safe Ride Rate = 
DIVIDE(
    CALCULATE(COUNTROWS('fact_trip_safety'), 'fact_trip_safety'[safe_ride_flag] = TRUE),
    COUNTROWS('fact_trip_safety')
) * 100

MTTD (Hours) = 
AVERAGE('fact_safety_regressions'[mttd_hours])

Critical Events Count = 
SUM('fact_trip_safety'[critical_events])

Total Trips = 
COUNTROWS('fact_trip_safety')
```

---

### Page 2: Safety Regression Analysis
**Purpose**: Deep dive into detected safety regressions

#### Visuals:
1. **Regression Timeline**
   - Gantt chart: Regression episodes over time
   - X-axis: Date
   - Y-axis: Vehicle ID
   - Color: Hazard Ratio (gradient)
   - Tooltip: Start/End, Duration, MTTD, Affected Trips

2. **Hazard Rate Comparison**
   - Clustered column chart
   - Categories: Baseline vs Regression
   - Series: By Vehicle
   - Error bars: Credible intervals

3. **MTTD Distribution**
   - Histogram: MTTD hours distribution
   - Bins: 0-24h, 24-72h, 72-168h, >168h
   - Color: MTTD Category (Excellent/Good/Acceptable/Poor)

4. **Regression Detection Methods**
   - Pie chart: Detection method breakdown
   - Categories: Change-point, Threshold, Manual

5. **Affected Trips Table**
   - Columns: Trip ID, Vehicle, Date, Events, Safety Score
   - Filter: By Regression ID
   - Export: CSV

#### Measures:
```dax
Average MTTD = 
AVERAGE('fact_safety_regressions'[mttd_hours])

Hazard Ratio = 
AVERAGE('fact_safety_regressions'[hazard_ratio])

Regression Duration (Hours) = 
AVERAGE('fact_safety_regressions'[regression_duration_hours])
```

---

### Page 3: Rare Event Detection
**Purpose**: Analyze rare failure modes and detection sensitivity

#### Visuals:
1. **Rare Event Timeline**
   - Line chart: Rare event count over time
   - X-axis: Date
   - Y-axis: Rare Event Count
   - Series: By Event Type
   - Annotations: Regression periods

2. **Rare Event Type Distribution**
   - Treemap: Event types by frequency
   - Size: Event count
   - Color: Severity

3. **Detection Sensitivity Comparison**
   - Clustered bar chart
   - Categories: Sampling Methods (Uniform, Stratified, Importance, Adaptive)
   - Values: Sensitivity, False Positive Rate, MTTD
   - Reference line: Baseline (Uniform)

4. **Rare Event by Vehicle**
   - Matrix: Vehicle × Event Type
   - Values: Event count, Affected trips
   - Conditional formatting: Heat map

5. **Importance Sampling Results Table**
   - Columns: Method, Sensitivity, FPR, MTTD, Improvement %
   - Sort: By Sensitivity (descending)

#### Measures:
```dax
Rare Event Rate = 
DIVIDE(
    SUM('fact_trip_safety'[rare_event_count]),
    COUNTROWS('fact_trip_safety')
) * 1000  -- Per 1000 trips

Detection Sensitivity = 
AVERAGE('model_importance_sampling_results'[detection_sensitivity])

MTTD Improvement = 
AVERAGE('model_importance_sampling_results'[mttd_improvement_pct])
```

---

### Page 4: Vehicle Performance
**Purpose**: Vehicle-level safety performance analysis

#### Visuals:
1. **Vehicle Safety Score Ranking**
   - Bar chart: All vehicles sorted by safety score
   - Color: By Vehicle Model
   - Tooltip: Total trips, Events, Rare events

2. **Safety Score Trend by Vehicle**
   - Line chart: Safety score over time
   - X-axis: Date
   - Y-axis: Safety Score
   - Series: Selected vehicles (multi-select)
   - Slicer: Vehicle ID

3. **Event Rate by Vehicle**
   - Scatter plot
   - X-axis: Total Events per Trip
   - Y-axis: Critical Events per Trip
   - Size: Total Trips
   - Color: Vehicle Model
   - Reference lines: Thresholds

4. **Latency Analysis**
   - Box plot: Latency distribution by vehicle
   - Y-axis: Latency (ms)
   - X-axis: Vehicle ID
   - Outliers: Highlighted

5. **Vehicle Details Table**
   - Columns: Vehicle ID, Model, Firmware, Total Trips, Safety Score, Events, Rare Events
   - Filter: By date range, model, firmware
   - Export: CSV

#### Measures:
```dax
Events per Trip = 
DIVIDE(
    SUM('fact_trip_safety'[total_events]),
    COUNTROWS('fact_trip_safety')
)

Average Safety Score = 
AVERAGE('fact_trip_safety'[safety_score])

Average Latency = 
AVERAGE('fact_trip_safety'[avg_latency_ms])
```

---

### Page 5: Model Diagnostics
**Purpose**: Monitor model performance and convergence

#### Visuals:
1. **Model Convergence Status**
   - Card: % Models Converged (R-hat < 1.01)
   - Gauge: Overall convergence rate

2. **R-hat Distribution**
   - Histogram: R-hat values across models
   - Reference line: 1.01 (convergence threshold)
   - Color: Converged (green) / Not Converged (red)

3. **Effective Sample Size**
   - Bar chart: ESS by model run
   - Reference line: 400 (minimum recommended)
   - Sort: Ascending (lowest first)

4. **Model Run History**
   - Table: Model runs with diagnostics
   - Columns: Run ID, Timestamp, Model Type, Convergence, R-hat Max, Min ESS
   - Filter: Last 30 days

5. **Posterior Predictive Check**
   - Line chart: Observed vs Predicted event rates
   - X-axis: Time
   - Series: Observed, Predicted (mean), Credible intervals

#### Measures:
```dax
Convergence Rate = 
DIVIDE(
    CALCULATE(COUNTROWS('model_survival_outputs'), 'model_survival_outputs'[convergence_flag] = TRUE),
    COUNTROWS('model_survival_outputs')
) * 100

Average R-hat = 
AVERAGE('model_survival_outputs'[rhat_max])

Min ESS = 
MIN('model_survival_outputs'[effective_sample_size])
```

---

## Slicers (Global)
Applied across all pages:
- **Date Range**: Last 7/30/90 days, Custom range
- **Vehicle Model**: Multi-select
- **Firmware Version**: Multi-select
- **Operating Mode**: Autonomous/Manual/Transition
- **Event Severity**: Critical/Warning/Info

## Drill-Through Pages
1. **Event Details**: From any event count → Detailed event table
2. **Trip Details**: From trip metrics → Individual trip breakdown
3. **Regression Details**: From regression alert → Full regression analysis

## Alerts & Notifications
- **Email Alerts**: Daily summary of new regressions
- **Power BI Alerts**: Threshold-based (e.g., MTTD > 72 hours)
- **Mobile App**: Push notifications for critical regressions

## Performance Optimization
- **Aggregations**: Pre-aggregated tables for common queries
- **Incremental Refresh**: Only load new data daily
- **Query Folding**: Push filters to BigQuery
- **Composite Models**: Mix DirectQuery and Import for optimal performance

## Security
- **Row-Level Security**: Filter by user's vehicle access
- **Data Classification**: Mark sensitive fields
- **Audit Logging**: Track dashboard access

## Mobile Layout
- Responsive design for mobile devices
- Key metrics on first screen
- Simplified visuals for small screens
- Touch-optimized interactions
