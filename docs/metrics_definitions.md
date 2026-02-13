# Metric Definitions

## Core Safety Metrics

### Safe Ride Rate
**Definition**: Percentage of trips completed without any critical safety events.

**Formula**:
```
Safe Ride Rate = (Number of trips with no critical events / Total trips) × 100
```

**Calculation**:
```sql
SELECT 
    COUNT(CASE WHEN critical_events = 0 THEN 1 END) * 100.0 / COUNT(*) AS safe_ride_rate
FROM fact_trip_safety
```

**Interpretation**:
- Higher is better
- Target: >95%
- Used for: Overall safety health, trend monitoring

---

### Mean Time To Detection (MTTD)
**Definition**: Average time from the onset of a safety regression to its detection.

**Formula**:
```
MTTD = Average(detection_timestamp - regression_start_timestamp)
```

**Calculation**:
```sql
SELECT 
    AVG(TIMESTAMP_DIFF(detection_timestamp, regression_start_timestamp, HOUR)) AS mttd_hours
FROM fact_safety_regressions
WHERE changepoint_detected = TRUE
```

**Interpretation**:
- Lower is better
- Target: <24 hours (excellent), <72 hours (good), <168 hours (acceptable)
- Used for: Detection system performance, regression response time

**Categories**:
- Excellent: <24 hours
- Good: 24-72 hours
- Acceptable: 72-168 hours
- Poor: >168 hours

---

### Safety Regression
**Definition**: A significant increase in the hazard rate of critical safety events, indicating a degradation in system safety performance.

**Detection Criteria**:
1. Change-point model detects a shift in hazard rate
2. Hazard ratio > 1.5 (50% increase)
3. Statistical significance (credible interval excludes 1.0)

**Formula**:
```
Hazard Ratio = post_change_hazard_rate / baseline_hazard_rate
```

**Interpretation**:
- Hazard ratio > 1.5: Regression detected
- Hazard ratio < 1.0: Improvement detected
- Used for: Safety monitoring, alerting, investigation triggers

---

### Safety Score
**Definition**: Composite metric (0-100) representing overall trip safety, where higher scores indicate safer trips.

**Formula**:
```
Safety Score = max(0, 100 - (critical_events × 20) - (total_events × 2))
```

**Calculation**:
```sql
SELECT 
    GREATEST(0, 100 - (critical_events * 20) - (total_events * 2)) AS safety_score
FROM fact_trip_safety
```

**Interpretation**:
- Range: 0-100
- Higher is better
- Penalties:
  - Critical event: -20 points
  - Any event: -2 points
- Used for: Trip ranking, vehicle comparison, trend analysis

---

### Rare Event Rate
**Definition**: Rate of rare safety-critical events per 1000 trips.

**Formula**:
```
Rare Event Rate = (Total rare events / Total trips) × 1000
```

**Calculation**:
```sql
SELECT 
    SUM(rare_event_count) * 1000.0 / COUNT(*) AS rare_event_rate_per_1000
FROM fact_trip_safety
```

**Interpretation**:
- Lower is better
- Typical range: 0.1-10 per 1000 trips
- Used for: Rare failure mode monitoring, importance sampling evaluation

---

## Detection Metrics

### Detection Sensitivity (True Positive Rate)
**Definition**: Proportion of actual safety regressions that are correctly detected.

**Formula**:
```
Sensitivity = True Positives / (True Positives + False Negatives)
```

**Interpretation**:
- Range: 0-1 (or 0-100%)
- Higher is better
- Target: >0.8 (80%)
- Used for: Model evaluation, importance sampling comparison

---

### False Positive Rate
**Definition**: Proportion of non-regressions incorrectly flagged as regressions.

**Formula**:
```
FPR = False Positives / (False Positives + True Negatives)
```

**Interpretation**:
- Range: 0-1 (or 0-100%)
- Lower is better
- Target: <0.1 (10%)
- Used for: Model evaluation, alert tuning

---

### MTTD Improvement
**Definition**: Percentage reduction in MTTD achieved by a detection method compared to baseline.

**Formula**:
```
MTTD Improvement % = ((Baseline MTTD - Method MTTD) / Baseline MTTD) × 100
```

**Interpretation**:
- Positive: Improvement (lower MTTD)
- Negative: Degradation (higher MTTD)
- Used for: Importance sampling evaluation, method comparison

---

## Model Diagnostics

### R-hat (Gelman-Rubin Statistic)
**Definition**: Convergence diagnostic for MCMC chains. Values close to 1.0 indicate convergence.

**Formula**:
```
R-hat = sqrt(Variance between chains / Variance within chains)
```

**Interpretation**:
- R-hat < 1.01: Converged (good)
- R-hat 1.01-1.05: Acceptable
- R-hat > 1.05: Not converged (problematic)
- Used for: Model validation, quality assurance

---

### Effective Sample Size (ESS)
**Definition**: Number of independent samples equivalent to the MCMC samples, accounting for autocorrelation.

**Interpretation**:
- Higher is better
- Minimum recommended: 400
- Used for: Model validation, sample quality assessment

---

## Event Metrics

### Events per Trip
**Definition**: Average number of events (all types) per trip.

**Formula**:
```
Events per Trip = Total events / Total trips
```

**Calculation**:
```sql
SELECT 
    SUM(total_events) * 1.0 / COUNT(*) AS events_per_trip
FROM fact_trip_safety
```

**Interpretation**:
- Lower is better
- Typical range: 0.5-5 events/trip
- Used for: System health monitoring

---

### Critical Events per Trip
**Definition**: Average number of critical events per trip.

**Formula**:
```
Critical Events per Trip = Total critical events / Total trips
```

**Interpretation**:
- Lower is better
- Target: <0.1 per trip
- Used for: Safety monitoring, alerting

---

### Average Latency
**Definition**: Mean system latency across all events.

**Formula**:
```
Average Latency = Sum(latency_ms) / Count(events)
```

**Calculation**:
```sql
SELECT 
    AVG(avg_latency_ms) AS avg_latency_ms
FROM fact_trip_safety
```

**Interpretation**:
- Lower is better
- Target: <100ms
- Used for: Performance monitoring, system health

---

## Hazard Metrics

### Baseline Hazard Rate
**Definition**: Expected rate of safety events under normal operating conditions.

**Formula**:
```
Baseline Hazard Rate = (Events / Exposure) in baseline period
```

**Interpretation**:
- Units: Events per trip (or per hour)
- Used for: Regression detection, comparison baseline

---

### Regression Hazard Rate
**Definition**: Observed rate of safety events during a regression period.

**Formula**:
```
Regression Hazard Rate = (Events / Exposure) in regression period
```

**Interpretation**:
- Units: Events per trip (or per hour)
- Used for: Regression characterization, severity assessment

---

### Hazard Ratio
**Definition**: Ratio of regression hazard rate to baseline hazard rate.

**Formula**:
```
Hazard Ratio = Regression Hazard Rate / Baseline Hazard Rate
```

**Interpretation**:
- HR = 1.0: No change
- HR > 1.0: Increase (regression)
- HR < 1.0: Decrease (improvement)
- Threshold: HR > 1.5 indicates regression
- Used for: Regression detection, alerting

---

## Data Quality Metrics

### Data Completeness
**Definition**: Percentage of expected records that are present.

**Formula**:
```
Completeness = (Actual records / Expected records) × 100
```

**Interpretation**:
- Target: >99%
- Used for: Data quality monitoring

---

### Data Freshness
**Definition**: Time since last data update.

**Formula**:
```
Freshness = Current timestamp - Max(ingestion_timestamp)
```

**Interpretation**:
- Target: <24 hours
- Used for: Pipeline monitoring, alerting

---

## Notes

- All timestamps are in UTC
- All durations are in hours unless specified
- Percentages are displayed as 0-100 (not 0-1)
- Credible intervals are 95% unless specified
- Metrics are computed daily after pipeline completion
