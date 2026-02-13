# Data Dictionary

## Staging Tables

### staging_trips
Raw trip telemetry data.

| Column | Type | Description |
|--------|------|-------------|
| trip_id | STRING | Unique trip identifier |
| vehicle_id | STRING | Vehicle identifier |
| driver_id | STRING | Driver identifier (nullable) |
| start_timestamp | TIMESTAMP | Trip start time (UTC) |
| end_timestamp | TIMESTAMP | Trip end time (UTC) |
| start_location_lat | FLOAT64 | Start latitude |
| start_location_lon | FLOAT64 | Start longitude |
| end_location_lat | FLOAT64 | End latitude |
| end_location_lon | FLOAT64 | End longitude |
| trip_distance_km | FLOAT64 | Trip distance in kilometers |
| trip_duration_seconds | INT64 | Trip duration in seconds |
| operating_mode | STRING | 'autonomous', 'manual', 'transition' |
| weather_condition | STRING | Weather condition |
| road_type | STRING | Road type |
| ingestion_timestamp | TIMESTAMP | When data was ingested |
| source_file | STRING | Source file name |
| raw_data | JSON | Raw JSON data |

### staging_events
Raw event telemetry (safety events, faults, interventions).

| Column | Type | Description |
|--------|------|-------------|
| event_id | STRING | Unique event identifier |
| trip_id | STRING | Associated trip |
| vehicle_id | STRING | Vehicle identifier |
| event_timestamp | TIMESTAMP | Event occurrence time |
| event_type | STRING | Event type (see event_types) |
| event_severity | STRING | 'critical', 'warning', 'info' |
| event_category | STRING | 'perception', 'planning', 'control', 'system' |
| event_subcategory | STRING | Event subcategory |
| event_description | STRING | Human-readable description |
| intervention_type | STRING | 'takeover', 'brake', 'steer', 'none' |
| fault_code | STRING | Fault code (if applicable) |
| latency_ms | FLOAT64 | System latency in milliseconds |
| confidence_score | FLOAT64 | Model confidence (0-1) |
| sensor_data | JSON | Sensor data payload |
| metadata | JSON | Additional metadata |
| ingestion_timestamp | TIMESTAMP | When data was ingested |
| source_file | STRING | Source file name |

### staging_mode_transitions
Raw mode transition events.

| Column | Type | Description |
|--------|------|-------------|
| transition_id | STRING | Unique transition identifier |
| trip_id | STRING | Associated trip |
| vehicle_id | STRING | Vehicle identifier |
| transition_timestamp | TIMESTAMP | Transition time |
| from_mode | STRING | Source mode |
| to_mode | STRING | Target mode |
| transition_reason | STRING | Reason for transition |
| transition_duration_seconds | FLOAT64 | Transition duration |
| context_data | JSON | Context information |
| ingestion_timestamp | TIMESTAMP | When data was ingested |
| source_file | STRING | Source file name |

## Dimension Tables

### dim_vehicles
Vehicle dimension (SCD Type 2).

| Column | Type | Description |
|--------|------|-------------|
| vehicle_id | STRING | Vehicle identifier (PK) |
| vehicle_model | STRING | Vehicle model |
| vehicle_year | INT64 | Model year |
| firmware_version | STRING | Firmware version |
| hardware_config | STRING | Hardware configuration |
| first_seen_date | DATE | First trip date |
| last_seen_date | DATE | Last trip date |
| total_trips | INT64 | Total trips (snapshot) |
| valid_from | TIMESTAMP | SCD valid from |
| valid_to | TIMESTAMP | SCD valid to |
| is_current | BOOL | Current version flag |

### dim_drivers
Driver dimension (SCD Type 2).

| Column | Type | Description |
|--------|------|-------------|
| driver_id | STRING | Driver identifier (PK) |
| driver_experience_years | INT64 | Years of experience |
| driver_category | STRING | 'professional', 'consumer', 'test' |
| first_seen_date | DATE | First trip date |
| last_seen_date | DATE | Last trip date |
| valid_from | TIMESTAMP | SCD valid from |
| valid_to | TIMESTAMP | SCD valid to |
| is_current | BOOL | Current version flag |

### dim_time
Time dimension (date attributes).

| Column | Type | Description |
|--------|------|-------------|
| date_key | DATE | Date (PK) |
| year | INT64 | Year |
| quarter | INT64 | Quarter (1-4) |
| month | INT64 | Month (1-12) |
| week | INT64 | Week number |
| day_of_year | INT64 | Day of year (1-366) |
| day_of_month | INT64 | Day of month (1-31) |
| day_of_week | INT64 | Day of week (1=Sunday) |
| is_weekend | BOOL | Weekend flag |
| is_holiday | BOOL | Holiday flag |
| fiscal_year | INT64 | Fiscal year |
| fiscal_quarter | INT64 | Fiscal quarter |

### dim_event_types
Event type dimension.

| Column | Type | Description |
|--------|------|-------------|
| event_type_key | STRING | Event type (PK) |
| event_type | STRING | Event type name |
| event_category | STRING | Event category |
| event_severity | STRING | Typical severity |
| is_critical | BOOL | Critical event flag |
| is_rare_event | BOOL | Rare event flag |
| description | STRING | Description |

## Fact Tables

### fact_trip_safety
Trip-level safety metrics (grain: one row per trip).

| Column | Type | Description |
|--------|------|-------------|
| trip_id | STRING | Trip identifier (PK) |
| vehicle_id | STRING | Vehicle (FK to dim_vehicles) |
| driver_id | STRING | Driver (FK to dim_drivers) |
| date_key | DATE | Date (FK to dim_time) |
| start_timestamp | TIMESTAMP | Trip start |
| end_timestamp | TIMESTAMP | Trip end |
| trip_duration_seconds | INT64 | Duration |
| trip_distance_km | FLOAT64 | Distance |
| operating_mode | STRING | Operating mode |
| total_events | INT64 | Total events in trip |
| critical_events | INT64 | Critical events |
| safety_interventions | INT64 | Safety interventions |
| mode_transitions | INT64 | Mode transitions |
| max_latency_ms | FLOAT64 | Maximum latency |
| avg_latency_ms | FLOAT64 | Average latency |
| has_rare_event | BOOL | Contains rare event |
| rare_event_count | INT64 | Rare event count |
| safe_ride_flag | BOOL | No critical events |
| safety_score | FLOAT64 | Safety score (0-100) |
| load_timestamp | TIMESTAMP | When loaded |

### fact_events
Event-level details (grain: one row per event).

| Column | Type | Description |
|--------|------|-------------|
| event_id | STRING | Event identifier (PK) |
| trip_id | STRING | Trip (FK to fact_trip_safety) |
| vehicle_id | STRING | Vehicle (FK to dim_vehicles) |
| driver_id | STRING | Driver (FK to dim_drivers) |
| date_key | DATE | Date (FK to dim_time) |
| event_timestamp | TIMESTAMP | Event time |
| event_type_key | STRING | Event type (FK to dim_event_types) |
| event_severity | STRING | Severity |
| intervention_type | STRING | Intervention type |
| latency_ms | FLOAT64 | Latency |
| confidence_score | FLOAT64 | Confidence |
| is_rare_event | BOOL | Rare event flag |
| time_since_trip_start_seconds | FLOAT64 | Time from trip start |
| time_since_last_event_seconds | FLOAT64 | Time from last event |
| events_in_trip_before | INT64 | Event sequence number |
| load_timestamp | TIMESTAMP | When loaded |

### fact_safety_regressions
Safety regression episodes (grain: one row per regression).

| Column | Type | Description |
|--------|------|-------------|
| regression_id | STRING | Regression identifier (PK) |
| vehicle_id | STRING | Vehicle (FK to dim_vehicles) |
| date_key | DATE | Date (FK to dim_time) |
| regression_start_timestamp | TIMESTAMP | Regression start |
| regression_end_timestamp | TIMESTAMP | Regression end |
| regression_duration_hours | FLOAT64 | Duration in hours |
| detection_timestamp | TIMESTAMP | When detected |
| mttd_hours | FLOAT64 | Mean Time To Detection |
| detection_method | STRING | Detection method |
| baseline_hazard_rate | FLOAT64 | Baseline hazard |
| regression_hazard_rate | FLOAT64 | Regression hazard |
| hazard_ratio | FLOAT64 | Hazard ratio |
| affected_trips | INT64 | Affected trips |
| affected_events | INT64 | Affected events |
| is_resolved | BOOL | Resolved flag |
| resolution_timestamp | TIMESTAMP | Resolution time |
| load_timestamp | TIMESTAMP | When loaded |

## Model Output Tables

### model_survival_outputs
Survival model predictions.

| Column | Type | Description |
|--------|------|-------------|
| model_run_id | STRING | Model run identifier |
| model_run_timestamp | TIMESTAMP | Run time |
| vehicle_id | STRING | Vehicle |
| date_key | DATE | Date |
| baseline_hazard_rate | FLOAT64 | Baseline hazard |
| hazard_rate_lower_ci | FLOAT64 | Lower CI |
| hazard_rate_upper_ci | FLOAT64 | Upper CI |
| predicted_time_to_event_hours | FLOAT64 | Predicted TTE |
| predicted_time_lower_ci | FLOAT64 | Lower CI |
| predicted_time_upper_ci | FLOAT64 | Upper CI |
| convergence_flag | BOOL | Converged |
| rhat_max | FLOAT64 | Max R-hat |
| effective_sample_size | INT64 | ESS |
| model_version | STRING | Model version |
| hyperparameters | JSON | Hyperparameters |

### model_changepoint_outputs
Change-point detection results.

| Column | Type | Description |
|--------|------|-------------|
| model_run_id | STRING | Model run identifier |
| model_run_timestamp | TIMESTAMP | Run time |
| vehicle_id | STRING | Vehicle |
| date_key | DATE | Date |
| changepoint_detected | BOOL | Detected flag |
| changepoint_timestamp | TIMESTAMP | Change-point time |
| changepoint_probability | FLOAT64 | Detection probability |
| pre_change_hazard_rate | FLOAT64 | Pre-change hazard |
| post_change_hazard_rate | FLOAT64 | Post-change hazard |
| hazard_ratio | FLOAT64 | Hazard ratio |
| hazard_ratio_lower_ci | FLOAT64 | Lower CI |
| hazard_ratio_upper_ci | FLOAT64 | Upper CI |
| convergence_flag | BOOL | Converged |
| rhat_max | FLOAT64 | Max R-hat |
| model_version | STRING | Model version |
| hyperparameters | JSON | Hyperparameters |

### model_importance_sampling_results
Importance sampling experiment results.

| Column | Type | Description |
|--------|------|-------------|
| experiment_id | STRING | Experiment identifier |
| experiment_timestamp | TIMESTAMP | Experiment time |
| sampling_method | STRING | Method name |
| rare_event_rate | FLOAT64 | Rare event rate |
| sample_size | INT64 | Sample size |
| reweighting_scheme | STRING | Reweighting scheme |
| detection_sensitivity | FLOAT64 | Sensitivity (TPR) |
| false_positive_rate | FLOAT64 | FPR |
| mttd_hours | FLOAT64 | MTTD |
| mttd_improvement_pct | FLOAT64 | MTTD improvement % |
| p_value | FLOAT64 | P-value |
| effect_size | FLOAT64 | Effect size |
| experiment_config | JSON | Configuration |

## Alert Tables

### alerts
Safety alerts.

| Column | Type | Description |
|--------|------|-------------|
| alert_id | STRING | Alert identifier (PK) |
| alert_timestamp | TIMESTAMP | Alert time |
| alert_type | STRING | Alert type |
| severity | STRING | Severity |
| vehicle_id | STRING | Vehicle |
| trip_id | STRING | Trip |
| event_id | STRING | Event |
| regression_id | STRING | Regression |
| alert_message | STRING | Message |
| alert_metric | STRING | Metric name |
| alert_value | FLOAT64 | Metric value |
| alert_threshold | FLOAT64 | Threshold |
| is_acknowledged | BOOL | Acknowledged |
| acknowledged_by | STRING | Acknowledger |
| acknowledged_timestamp | TIMESTAMP | Acknowledgment time |
| is_resolved | BOOL | Resolved |
| resolved_timestamp | TIMESTAMP | Resolution time |
| source_model_run_id | STRING | Source model run |
| notification_sent | BOOL | Notification sent |
