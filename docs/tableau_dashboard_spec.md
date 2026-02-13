# Tableau Dashboard Specification

## Overview
Interactive Tableau dashboard for weekly safety investigations, providing real-time visibility into fleet safety metrics, rare event detection, change-point analysis, and MTTD improvements.

## Data Sources
- **CSV Extracts**: Located in `tableau/extracts/`
  - `fleet_safety_overview.csv` - Daily fleet metrics
  - `rare_event_monitoring.csv` - Rare event details
  - `changepoint_detection.csv` - Change-point detection results
  - `mttd_comparison.csv` - MTTD comparison by method
  - `vehicle_details.csv` - Vehicle metadata

- **Refresh Schedule**: Daily (after Airflow pipeline completion)
- **Connection Type**: Text file (CSV) extracts

---

## Page 1: Fleet Safety Overview

### Purpose
High-level safety KPIs and trends for executive review and weekly safety meetings.

### Visuals

#### 1. KPI Cards (Top Row)
- **Total Trips** (Last 7 Days)
  - Calculation: `SUM([Total Trips])`
  - Filter: Date >= TODAY() - 7
  
- **Safe Ride Rate** (%)
  - Calculation: `AVG([Safe Ride Rate]) * 100`
  - Format: Percentage, 1 decimal
  
- **Active Vehicles**
  - Calculation: `COUNTD([Vehicle ID])`
  
- **Critical Events** (Last 7 Days)
  - Calculation: `SUM([Critical Events])`
  - Color: Red if > threshold
  
- **MTTD** (Hours)
  - Calculation: `AVG([MTTD Hours])`
  - Data Source: Change-Point Detection

#### 2. Safety Trend Line Chart
- **X-axis**: Date (continuous)
- **Y-axis**: Safe Ride Rate (%)
- **Series**: 
  - Overall (line)
  - By Vehicle Model (multiple lines, optional)
- **Markers**: Show data points
- **Reference Line**: Target (95%)
- **Tooltip**: Date, Safe Ride Rate, Total Trips

#### 3. Event Distribution Donut Chart
- **Categories**: 
  - Critical Events
  - Warnings
  - Info Events
- **Calculation**: `SUM([Total Events])` grouped by severity
- **Color**: Gradient (red → yellow → green)
- **Action**: Click to filter Page 2 (Rare Event Monitoring)

#### 4. Safety Score Trend
- **Chart Type**: Area chart
- **X-axis**: Date
- **Y-axis**: Average Safety Score
- **Color**: Gradient (green → yellow → red) based on score
- **Reference Lines**: 
  - Excellent: 90
  - Good: 80
  - Acceptable: 70

#### 5. Weekly Summary Table
- **Columns**: 
  - Week
  - Total Trips
  - Safe Ride Rate
  - Critical Events
  - Rare Events
  - Avg Safety Score
- **Sort**: Week (descending)
- **Highlight**: Current week

### Filters
- **Date Range**: Relative date filter (Last 7/30/90 days, Custom)
- **Vehicle Model**: Multi-select
- **Firmware Version**: Multi-select

---

## Page 2: Rare Event Monitoring

### Purpose
Deep dive into rare failure modes, their distribution, and patterns.

### Visuals

#### 1. Rare Event Timeline
- **Chart Type**: Line chart with markers
- **X-axis**: Date
- **Y-axis**: Rare Event Count
- **Series**: By Failure Mode (color)
- **Annotations**: Regression periods (from Page 3)
- **Tooltip**: Date, Failure Mode, Vehicle ID, Latency, Intervention

#### 2. Failure Mode Distribution
- **Chart Type**: Treemap
- **Size**: Count of events
- **Color**: By Event Category
- **Labels**: Failure Mode, Count, Percentage
- **Action**: Click to filter other visuals

#### 3. Rare Events by Vehicle
- **Chart Type**: Heat map (Matrix)
- **Rows**: Vehicle ID
- **Columns**: Failure Mode
- **Color**: Count of events (gradient)
- **Text**: Count
- **Sort**: By total rare events (descending)

#### 4. Latency vs Intervention Scatter Plot
- **X-axis**: Latency (ms)
- **Y-axis**: Confidence Score
- **Color**: Intervention Type
- **Size**: Count of events
- **Reference Lines**: 
  - Latency threshold: 200ms
  - Confidence threshold: 0.5

#### 5. Rare Event Details Table
- **Columns**: 
  - Date
  - Vehicle ID
  - Failure Mode
  - Latency (ms)
  - Intervention Type
  - Confidence Score
  - Trip ID
- **Filter**: By Failure Mode, Date Range
- **Sort**: Date (descending)
- **Export**: CSV

### Calculated Fields

#### Intervention Rate
```
SUM(IF [Intervention Type] != "none" THEN 1 ELSE 0 END) / COUNT([Event ID])
```

#### Degraded Mode Rate
```
COUNTD(IF [Failure Mode] CONTAINS "DEGRADATION" THEN [Vehicle ID] END) / 
COUNTD([Vehicle ID])
```

#### Latency Bucket
```
IF [Latency (ms)] < 100 THEN "Low (<100ms)"
ELSEIF [Latency (ms)] < 200 THEN "Medium (100-200ms)"
ELSEIF [Latency (ms)] < 300 THEN "High (200-300ms)"
ELSE "Critical (>300ms)"
END
```

### Filters
- **Date Range**: Relative date filter
- **Failure Mode**: Multi-select
- **Vehicle ID**: Multi-select
- **Intervention Type**: Multi-select
- **Latency Bucket**: Multi-select (calculated field)

---

## Page 3: Change-Point Detection

### Purpose
Monitor daily failure rates and detect safety regressions in real-time.

### Visuals

#### 1. Daily Failure Rate Trend
- **Chart Type**: Line chart with markers
- **X-axis**: Date
- **Y-axis**: Daily Failure Rate (events per 100 trips)
- **Color**: 
  - Normal: Blue
  - Regression Detected: Red
- **Reference Lines**:
  - Baseline: 0.5
  - Regression Threshold: 1.5
- **Annotations**: Change-point detection markers

#### 2. Change-Point Detection Indicators
- **Chart Type**: Gantt chart / Timeline
- **X-axis**: Date
- **Y-axis**: Detection Status
- **Color**: 
  - Not Detected: Gray
  - Detected: Red (intensity by probability)
- **Size**: Change-Point Probability
- **Tooltip**: Date, Probability, Hazard Ratio, MTTD

#### 3. Hazard Ratio Over Time
- **Chart Type**: Bar chart
- **X-axis**: Date
- **Y-axis**: Hazard Ratio
- **Color**: 
  - < 1.0: Green (improvement)
  - 1.0 - 1.5: Yellow (normal)
  - > 1.5: Red (regression)
- **Reference Line**: 1.5 (regression threshold)

#### 4. MTTD Distribution
- **Chart Type**: Histogram
- **X-axis**: MTTD (Hours)
- **Bins**: 
  - 0-24 hours (Excellent)
  - 24-72 hours (Good)
  - 72-168 hours (Acceptable)
  - >168 hours (Poor)
- **Color**: By MTTD category
- **Tooltip**: Count, Percentage

#### 5. Change-Point Summary Table
- **Columns**:
  - Detection Date
  - Change-Point Date
  - MTTD (Hours)
  - Hazard Ratio
  - Probability
  - Status
- **Sort**: Detection Date (descending)
- **Highlight**: Recent detections

### Calculated Fields

#### Rolling 7-Day Failure Rate
```
WINDOW_AVG(SUM([Daily Failure Rate]), -6, 0)
```

#### Regression Status
```
IF [Hazard Ratio] > 1.5 AND [Change-Point Probability] > 0.5 
THEN "Regression Detected"
ELSEIF [Hazard Ratio] < 1.0 
THEN "Improvement"
ELSE "Normal"
END
```

### Filters
- **Date Range**: Relative date filter
- **Regression Status**: Multi-select (calculated field)
- **MTTD Category**: Multi-select

---

## Page 4: MTTD Comparison

### Purpose
Compare Mean Time To Detection across different sampling methods (baseline vs importance sampling).

### Visuals

#### 1. MTTD Comparison Bar Chart
- **Chart Type**: Grouped bar chart
- **X-axis**: Sampling Method
- **Y-axis**: Average MTTD (Hours)
- **Color**: By Method
  - Uniform: Gray (baseline)
  - Stratified: Blue
  - Importance: Green
  - Adaptive: Dark Green
- **Error Bars**: Standard deviation
- **Reference Line**: Baseline (Uniform) average

#### 2. Sensitivity Comparison
- **Chart Type**: Grouped bar chart
- **X-axis**: Sampling Method
- **Y-axis**: Sensitivity (True Positive Rate)
- **Color**: By Method
- **Reference Line**: Baseline sensitivity

#### 3. MTTD Improvement Percentage
- **Chart Type**: Bar chart
- **X-axis**: Sampling Method
- **Y-axis**: MTTD Improvement (%)
- **Color**: 
  - Positive: Green
  - Negative: Red
- **Reference Line**: 0%
- **Labels**: Show percentage

#### 4. MTTD Distribution by Method
- **Chart Type**: Box plot
- **X-axis**: Sampling Method
- **Y-axis**: MTTD (Hours)
- **Show**: Outliers, quartiles, median
- **Color**: By Method

#### 5. Method Performance Summary
- **Chart Type**: Scatter plot
- **X-axis**: MTTD (Hours)
- **Y-axis**: Sensitivity
- **Color**: Sampling Method
- **Size**: Number of detections
- **Labels**: Method name
- **Quadrants**: 
  - Top-left: Best (low MTTD, high sensitivity)
  - Bottom-right: Worst (high MTTD, low sensitivity)

### Calculated Fields

#### MTTD Improvement vs Baseline
```
[MTTD Hours] - 
WINDOW_AVG(IF [Method] = "uniform" THEN [MTTD Hours] END)
```

#### MTTD Improvement Percentage
```
([MTTD Improvement vs Baseline] / 
WINDOW_AVG(IF [Method] = "uniform" THEN [MTTD Hours] END)) * 100
```

### Filters
- **Sampling Method**: Multi-select
- **Date Range**: Relative date filter
- **Sensitivity Threshold**: Parameter (0.0 - 1.0)

### Parameters

#### Sensitivity Threshold
- **Name**: `Sensitivity Threshold`
- **Data Type**: Float
- **Current Value**: 0.8
- **Allowable Values**: Range 0.0 to 1.0
- **Use**: Filter methods above threshold

---

## Global Filters & Parameters

### Filters (Applied to All Pages)
- **Date Range**: 
  - Type: Relative date
  - Default: Last 30 days
  - Options: Last 7/30/90 days, Custom range
  
- **Vehicle Model**: 
  - Type: Multi-select
  - Source: Vehicle Details extract
  
- **Firmware Version**: 
  - Type: Multi-select
  - Source: Vehicle Details extract

### Parameters

#### Target Safe Ride Rate
- **Name**: `Target Safe Ride Rate`
- **Data Type**: Float
- **Current Value**: 0.95
- **Allowable Values**: Range 0.0 to 1.0
- **Use**: Reference line on Page 1

#### Regression Threshold
- **Name**: `Regression Threshold`
- **Data Type**: Float
- **Current Value**: 1.5
- **Allowable Values**: Range 1.0 to 3.0
- **Use**: Change-point detection threshold on Page 3

#### Latency Threshold
- **Name**: `Latency Threshold (ms)`
- **Data Type**: Integer
- **Current Value**: 200
- **Allowable Values**: Range 50 to 500
- **Use**: Alert threshold on Page 2

---

## Dashboard Actions

### Filter Actions
- **Page 1 → Page 2**: Filter Rare Event Monitoring by selected date range
- **Page 2 → Page 3**: Filter Change-Point Detection by failure mode
- **Page 3 → Page 1**: Filter Fleet Overview by regression period

### Highlight Actions
- Cross-page highlighting for Vehicle ID
- Cross-page highlighting for Date

### URL Actions
- Link to detailed trip analysis (if available)
- Link to vehicle maintenance records (if available)

---

## Weekly Safety Analyst Workflow

### Monday Morning Routine (30 minutes)

1. **Open Dashboard** → Page 1: Fleet Safety Overview
   - Check weekend KPIs (Total Trips, Safe Ride Rate)
   - Review safety score trend for anomalies
   - Identify any critical events spike

2. **Investigate Anomalies** → Page 3: Change-Point Detection
   - Check for new regression detections
   - Review MTTD for recent detections
   - If regression detected:
     - Note detection date and MTTD
     - Check hazard ratio and probability
     - Proceed to Page 2 for root cause

3. **Root Cause Analysis** → Page 2: Rare Event Monitoring
   - Filter by regression period (from Page 3)
   - Review failure mode distribution
   - Identify most common failure modes
   - Check latency patterns
   - Export rare event details for investigation

4. **Method Validation** → Page 4: MTTD Comparison
   - Review if importance sampling improved detection
   - Check if MTTD meets targets (<24 hours excellent)
   - Document method performance for weekly report

### Weekly Report Generation (1 hour)

1. **Executive Summary** (Page 1)
   - Screenshot of KPIs
   - Safety trend chart
   - Week-over-week comparison

2. **Regression Analysis** (Page 3)
   - List of detected regressions
   - MTTD summary
   - Hazard ratio trends

3. **Rare Event Summary** (Page 2)
   - Top 5 failure modes
   - Vehicle-level breakdown
   - Intervention patterns

4. **Method Performance** (Page 4)
   - MTTD improvement metrics
   - Sensitivity comparison
   - Recommendations for method selection

### Ad-Hoc Investigations

**When Alert Received**:
1. Navigate to Page 3 → Find alert date
2. Check change-point probability and hazard ratio
3. Navigate to Page 2 → Filter by date and failure mode
4. Export event details for engineering team
5. Update dashboard filters to monitor resolution

**When Vehicle Issue Reported**:
1. Navigate to Page 2 → Filter by Vehicle ID
2. Review rare event history
3. Check latency patterns
4. Compare to fleet average (Page 1)
5. Export vehicle-specific report

---

## Performance Optimization

### Data Source Optimization
- Use Tableau Data Extracts (.hyper) for faster performance
- Schedule extract refreshes daily (after Airflow pipeline)
- Incremental refresh for large datasets

### Dashboard Optimization
- Use context filters for frequently filtered dimensions
- Enable query caching
- Use data source filters for date ranges
- Limit data to last 90 days (archive older data)

### Mobile Layout
- Simplified KPI cards on mobile
- Single-column layout
- Touch-optimized filters
- Key metrics on first screen

---

## Security & Access

### Row-Level Security
- Filter by user's vehicle access (if implemented)
- Filter by user's region (if applicable)

### Data Classification
- Mark sensitive fields (Vehicle ID, Trip ID)
- Restrict export permissions if needed

---

## Maintenance

### Daily
- Verify extract refresh completed
- Check for data quality issues
- Review new regression detections

### Weekly
- Update calculated fields if metrics change
- Review filter performance
- Archive old data (>90 days)

### Monthly
- Review dashboard usage analytics
- Update parameter defaults if needed
- Optimize slow-performing queries

---

## Export & Sharing

### Export Formats
- PDF: For weekly reports
- Image: For presentations
- Data: CSV export for further analysis
- Workbook: For sharing with team

### Sharing Options
- Tableau Server/Online: For team access
- Tableau Public: For public demos (anonymized)
- Embedded: For integration with other tools

---

## Next Steps

1. **Connect Data Sources**: Link CSV extracts in Tableau
2. **Build Calculated Fields**: Create all calculated fields listed above
3. **Create Parameters**: Set up global parameters
4. **Build Pages**: Create 4 dashboard pages
5. **Add Filters**: Configure global and page-level filters
6. **Set Up Actions**: Configure filter and highlight actions
7. **Test Workflow**: Run through weekly analyst workflow
8. **Publish**: Deploy to Tableau Server/Online
9. **Schedule Refreshes**: Set up daily extract refresh
10. **Train Users**: Conduct dashboard training session
